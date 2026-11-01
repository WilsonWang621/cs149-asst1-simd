"""Record and plot the contiguous-row baseline for both Mandelbrot views."""

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


def main():
    destination = Path(__file__).resolve().parent
    root = destination.parents[1]
    project = root / "prog1_mandelbrot_threads"
    subprocess.run(["make", "-C", str(project)], check=True)

    metadata = [
        f"UTC start: {datetime.now(timezone.utc).isoformat()}",
        f"Platform: {platform.platform()}",
        "Policy: contiguous rows; image: 1600 x 1200; max iterations: 256",
        "Each executable invocation takes the minimum of five serial and five threaded runs.",
        "Configurations run sequentially, without CPU affinity pinning.",
    ]
    for command in (["g++", "--version"], ["lscpu"], ["git", "diff", "--", "prog1_mandelbrot_threads/mandelbrotThread.cpp"]):
        result = subprocess.run(command, cwd=root, capture_output=True, text=True, check=True)
        metadata.extend([f"$ {' '.join(command)}", result.stdout])
    (destination / "contiguous-environment.txt").write_text("\n".join(metadata), encoding="utf-8")

    rows = []
    with (destination / "contiguous-output.txt").open("w", encoding="utf-8") as raw:
        for view in (1, 2):
            for threads in range(2, 9):
                command = ["./mandelbrot", "--threads", str(threads), "--view", str(view)]
                result = subprocess.run(command, cwd=project, capture_output=True, text=True)
                raw.write(f"$ {' '.join(command)}\n{result.stdout}{result.stderr}Exit status: {result.returncode}\n\n")
                raw.flush()
                if result.returncode != 0 or "Mismatch" in result.stdout:
                    raise RuntimeError(f"Validation failed for view {view}, threads {threads}")
                serial = float(re.search(r"\[mandelbrot serial\]:\s*\[([\d.]+)\]", result.stdout)[1])
                parallel = float(re.search(r"\[mandelbrot thread\]:\s*\[([\d.]+)\]", result.stdout)[1])
                rows.append({"view": view, "threads": threads, "serial_ms": serial,
                             "parallel_ms": parallel, "speedup": round(serial / parallel, 6),
                             "validation": "PASS"})
                print(f"View {view}, {threads} threads: {serial / parallel:.3f}x, PASS", flush=True)

    with (destination / "contiguous-results.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    figure, axes = plt.subplots(1, 2, figsize=(11, 4.3), sharey=True)
    for view, axis in zip((1, 2), axes):
        selected = [row for row in rows if row["view"] == view]
        axis.plot([row["threads"] for row in selected], [row["speedup"] for row in selected],
                  "o-", label="Contiguous rows")
        axis.plot([2, 8], [2, 8], "--", color="gray", label="Ideal linear speedup")
        axis.set(title=f"View {view}", xlabel="Number of threads", xticks=range(2, 9))
        axis.grid(alpha=0.3)
        axis.legend()
    axes[0].set_ylabel("Speedup over serial")
    figure.suptitle("Mandelbrot: contiguous-row baseline")
    figure.tight_layout()
    figure.savefig(destination / "contiguous-speedup.png", dpi=180)
    plt.close(figure)


if __name__ == "__main__":
    main()
