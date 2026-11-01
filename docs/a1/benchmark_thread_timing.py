"""Measure worker imbalance without replacing the preserved baseline data."""

import csv
from datetime import datetime, timezone
import os
from pathlib import Path
import platform
import re
import subprocess
import tempfile

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "cs149-matplotlib"))
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main():
    destination = Path(__file__).resolve().parent
    root = destination.parents[1]
    project = root / "prog1_mandelbrot_threads"
    subprocess.run(["make", "-C", str(project)], check=True)
    metadata = [f"UTC start: {datetime.now(timezone.utc).isoformat()}",
                f"Platform: {platform.platform()}",
                "1600 x 1200 pixels; 256 maximum iterations; contiguous rows.",
                "Five repetitions per configuration; sequential configurations; no affinity pinning.",
                "Worker and overall intervals exclude timing output."]
    for command in (["g++", "--version"], ["lscpu"], ["git", "diff", "--", "prog1_mandelbrot_threads"]):
        result = subprocess.run(command, cwd=root, capture_output=True, text=True, check=True)
        metadata.extend([f"$ {' '.join(command)}", result.stdout])
    (destination / "thread-timing-environment.txt").write_text(
        "\n".join(line.rstrip() for line in "\n".join(metadata).splitlines()).rstrip() + "\n", encoding="utf-8")

    measurements, summaries = [], []
    with (destination / "thread-timing-output.txt").open("w", encoding="utf-8") as raw:
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
                    r"\[worker timing\] run=(\d+) thread=(\d+) start_row=(\d+) end_row=(\d+) elapsed_ms=([\d.]+)",
                    result.stdout)
                assert len(runs) == 5 and len(workers) == 5 * threads
                for run, thread, start, end, ms in workers:
                    measurements.append(dict(view=view, threads=threads, run=int(run), thread=int(thread),
                                             start_row=int(start), end_row=int(end), worker_ms=float(ms),
                                             overall_ms=runs[int(run)]))
                best_run = min(runs, key=runs.get)
                best_workers = [row["worker_ms"] for row in measurements
                                if row["view"] == view and row["threads"] == threads and row["run"] == best_run]
                serial = float(re.search(r"\[mandelbrot serial\]:\s*\[([\d.]+)\]", result.stdout)[1])
                summaries.append(dict(view=view, threads=threads, serial_ms=serial,
                                      parallel_ms=runs[best_run], speedup=serial / runs[best_run],
                                      best_run=best_run, min_worker_ms=min(best_workers),
                                      max_worker_ms=max(best_workers),
                                      max_over_min=max(best_workers) / min(best_workers),
                                      worker_balance=sum(best_workers) / (threads * max(best_workers)),
                                      validation="PASS"))
                print(f"View {view}, {threads} threads: PASS; worker max/min={max(best_workers) / min(best_workers):.2f}", flush=True)

    write_csv(destination / "thread-timing-workers.csv", measurements)
    write_csv(destination / "thread-timing-summary.csv", summaries)
    figure, axes = plt.subplots(1, 2, figsize=(10, 4), sharey=True)
    for view, axis in zip((1, 2), axes):
        best = next(row["best_run"] for row in summaries if row["view"] == view and row["threads"] == 3)
        selected = [row for row in measurements if row["view"] == view and row["threads"] == 3 and row["run"] == best]
        bars = axis.bar([row["thread"] for row in selected], [row["worker_ms"] for row in selected])
        axis.bar_label(bars, fmt="%.1f ms", padding=3)
        axis.set(title=f"View {view}: three threads, run {best}", xlabel="Thread ID", xticks=[0, 1, 2])
        axis.grid(axis="y", alpha=0.25)
    axes[0].set_ylabel("Worker elapsed time (ms)")
    axes[0].set_ylim(0, max(row["worker_ms"] for row in measurements if row["threads"] == 3) * 1.2)
    figure.tight_layout()
    figure.savefig(destination / "thread-timing-three-threads.png", dpi=180)
    plt.close(figure)


if __name__ == "__main__":
    main()
