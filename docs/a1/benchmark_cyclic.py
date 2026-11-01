"""Measure cyclic row ownership and compare it with the preserved baseline."""

import csv
from datetime import datetime, timezone
from pathlib import Path
import platform
import re
import subprocess

from benchmark_thread_timing import write_csv, plt


def main():
    destination = Path(__file__).resolve().parent
    root = destination.parents[1]
    project = root / "prog1_mandelbrot_threads"
    subprocess.run(["make", "-C", str(project)], check=True)
    metadata = [f"UTC start: {datetime.now(timezone.utc).isoformat()}",
                f"Platform: {platform.platform()}",
                "Policy: cyclic rows; 1600 x 1200 pixels; maximum iterations: 256.",
                "Five serial and five threaded repetitions per configuration.",
                "Configurations run sequentially without affinity pinning; no printing inside timed intervals."]
    for command in (["g++", "--version"], ["lscpu"], ["git", "diff", "--", "prog1_mandelbrot_threads"]):
        result = subprocess.run(command, cwd=root, capture_output=True, text=True, check=True)
        metadata.extend([f"$ {' '.join(command)}", result.stdout])
    (destination / "cyclic-environment.txt").write_text(
        "\n".join(line.rstrip() for line in "\n".join(metadata).splitlines()).rstrip() + "\n", encoding="utf-8")

    measurements, summaries = [], []
    with (destination / "cyclic-output.txt").open("w", encoding="utf-8") as raw:
        for view in (1, 2):
            for threads in range(2, 9):
                command = ["./mandelbrot", "--threads", str(threads), "--view", str(view)]
                result = subprocess.run(command, cwd=project, capture_output=True, text=True)
                raw.write(f"$ {' '.join(command)}\n{result.stdout}{result.stderr}Exit status: {result.returncode}\n")
                raw.flush()
                if result.returncode or "Mismatch" in result.stdout:
                    raise RuntimeError(f"Validation failed: view {view}, threads {threads}")
                runs = {int(run): float(ms) for run, ms in re.findall(
                    r"\[threaded run\] run=(\d+) elapsed_ms=([\d.]+)", result.stdout)}
                workers = re.findall(
                    r"\[worker timing\] run=(\d+) thread=(\d+) start_row=(\d+) end_row=(\d+) row_stride=(\d+) elapsed_ms=([\d.]+)",
                    result.stdout)
                assert len(runs) == 5 and len(workers) == 5 * threads
                for run, thread, start, end, stride, ms in workers:
                    measurements.append(dict(view=view, threads=threads, run=int(run), thread=int(thread),
                                             start_row=int(start), end_row=int(end), row_stride=int(stride),
                                             worker_ms=float(ms), overall_ms=runs[int(run)]))
                best = min(runs, key=runs.get)
                selected = [row["worker_ms"] for row in measurements
                            if row["view"] == view and row["threads"] == threads and row["run"] == best]
                serial = float(re.search(r"\[mandelbrot serial\]:\s*\[([\d.]+)\]", result.stdout)[1])
                summaries.append(dict(view=view, threads=threads, serial_ms=serial, parallel_ms=runs[best],
                                      speedup=serial / runs[best], best_run=best, min_worker_ms=min(selected),
                                      max_worker_ms=max(selected), max_over_min=max(selected) / min(selected),
                                      worker_balance=sum(selected) / (threads * max(selected)), validation="PASS"))
                print(f"View {view}, {threads} threads: {serial / runs[best]:.2f}x; worker max/min={max(selected) / min(selected):.2f}; PASS", flush=True)

    write_csv(destination / "cyclic-workers.csv", measurements)
    write_csv(destination / "cyclic-summary.csv", summaries)
    with (destination / "thread-timing-summary.csv").open() as stream:
        baseline = list(csv.DictReader(stream))
    figure, axes = plt.subplots(1, 2, figsize=(11, 4.3), sharey=True)
    for view, axis in zip((1, 2), axes):
        old = [row for row in baseline if int(row["view"]) == view]
        new = [row for row in summaries if row["view"] == view]
        axis.plot([int(row["threads"]) for row in old], [float(row["speedup"]) for row in old], "o-", label="Contiguous rows")
        axis.plot([row["threads"] for row in new], [row["speedup"] for row in new], "o-", label="Cyclic rows")
        axis.plot([2, 8], [2, 8], "--", color="gray", label="Ideal linear speedup")
        axis.set(title=f"View {view}", xlabel="Number of threads", xticks=range(2, 9))
        axis.grid(alpha=0.25)
        axis.legend()
    axes[0].set_ylabel("Speedup over serial")
    figure.tight_layout()
    figure.savefig(destination / "cyclic-comparison.png", dpi=180)
    plt.close(figure)


if __name__ == "__main__":
    main()
