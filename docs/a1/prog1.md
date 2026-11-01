# Program 1 Development Log

The latest completed stage is documented in [Mandelbrot: Measuring Thread Load Imbalance](thread-load-analysis.md). The [contiguous-row baseline](contiguous-baseline.md) preserves the earlier 2-to-8-thread measurements and speedup curves. The entries below record the development stages.

## 2026-11-02: Starter Program Baseline

- Built with `make` and ran `./mandelbrot` in `prog1_mandelbrot_threads/`.
- The serial implementation completed in 426.008 ms and generated `mandelbrot-serial.ppm`.
- The starter worker only printed a greeting and performed no image computation. The threaded result failed the pixel comparison at row 0, column 143 (expected 1, actual 0); the process exited with status 1.
- The reported threaded time of 0.134 ms measured thread creation, greeting output, and joining without image computation. It is not a valid image generation performance result.

## 2026-11-02: Two-Thread Top/Bottom Partition

### Implementation and Rationale

- Modified `workerThreadStart()` in `prog1_mandelbrot_threads/mandelbrotThread.cpp`.
- Thread 0 computes rows 0 through 599; thread 1 computes rows 600 through 1199 for the 1600 by 1200 image.
- The split uses `height / 2`, with any remaining row assigned to thread 1.
- Both workers call the existing `mandelbrotSerial()` with their assigned starting row and row count. This preserves the pixel calculation and coordinate mapping.
- Workers write to disjoint regions of the shared output array, so no locking is needed. The existing joins wait for completion.
- This implementation covers the requested two-thread configuration.

### Validation

Built successfully with `make`. Ran:

```sh
./mandelbrot --threads 2 --view 1
./mandelbrot --threads 2 --view 2
```

Both runs exited with status 0 and passed the built-in comparison of every output pixel against the serial result. `git diff --check` also passed.

### Performance

| View | Serial time (ms) | Two-thread time (ms) | Speedup |
| --- | ---: | ---: | ---: |
| 1 | 421.439 | 210.748 | 2.00x |
| 2 | 237.042 | 140.476 | 1.69x |

Each reported time is the minimum of five executions. The timed sections cover image computation; the threaded section also includes thread creation and joining. Output allocation, clearing, image file writing, and result verification are outside these sections. Speedup is the minimum serial time divided by the minimum threaded time.

These measurements were collected in the current local workspace environment, not verified as a Stanford myth machine. Hardware details were not recorded for these runs.

## 2026-11-02: PNG Previews

- Converted the current `mandelbrot-serial.ppm` and `mandelbrot-thread.ppm` files to PNG with Pillow for convenient previewing. The PNG files are alongside the originals in `prog1_mandelbrot_threads/`.
- Both images show View 2, the last view rendered; its run overwrote the View 1 PPM files.
- No source code was changed and no new performance measurements were taken.

## 2026-11-02: Repository Tracking

- Prepared the Program 1 source changes, development log, collaboration rules, and ignore rules for a Git commit.
- Added generated Program 1 PNG previews to `.gitignore`. Existing rules already exclude executables, object files, PPM output, local toolchains, and the Python environment.
- Included the existing `main.cpp` comment correction so it accurately describes the five timing repetitions.
- No new performance measurements were taken.

## 2026-11-02: Generalized Contiguous Blocks

The two-thread split was extended to a shared integer-boundary rule for all supported thread counts. Both views passed full-image validation with 2 through 8 threads. An instrumented coverage check also passed all 192 configurations, including non-divisible heights and empty blocks. Eight-thread speedups were 4.10x for View 1 and 4.21x for View 2.

The [baseline report](contiguous-baseline.md) explains the implementation and measurement method for readers. Raw output, CSV data, the plot, and reproducibility tools are stored directly in this directory. The stage is preserved by the Git tag `prog1-contiguous-baseline` for comparison with future optimizations.

## 2026-11-02: Per-Thread Timing and Load Analysis

Added entry/exit timing to each worker and returned measurements to the main thread for output after the overall timer stops. The row partition and pixel computation are unchanged. All 14 view/thread configurations passed image validation; 350 worker measurements were recorded across five repetitions per configuration. The instrumented implementation also passed all 192 row-coverage checks.

View 1's three-thread measurement confirms the suspected load imbalance: the middle worker took 252.830 ms, while the outer workers took 81.109 ms and 81.895 ms. The resulting 1.65x speedup reproduces the earlier three-thread dip. View 2's corresponding durations were 106.617 ms, 65.640 ms, and 61.043 ms. The [analysis report](thread-load-analysis.md) relates these results to pixel brightness, iteration counts, and the preserved speedup curves. New data and plots use the `thread-timing-*` prefix to preserve the previous baseline artifacts.
