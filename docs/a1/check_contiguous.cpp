// Verify row coverage using the actual worker and thread-launching code.
#include <atomic>
#include <cstdio>
#include <initializer_list>
#include "../../prog1_mandelbrot_threads/mandelbrotThread.cpp"

static std::atomic<int> visits[1201];
static std::atomic<bool> invalid;

void mandelbrotSerial(float, float, float, float, int, int height,
                      int startRow, int numRows, int, int[]) {
    if (startRow < 0 || numRows < 0 || startRow + numRows > height) {
        invalid = true;
        return;
    }
    for (int row = startRow; row < startRow + numRows; ++row)
        ++visits[row];
}

int main() {
    int cases = 0;
    for (int height : {0, 1, 7, 1199, 1200, 1201}) {
        for (int threads = 1; threads <= 32; ++threads) {
            for (auto& count : visits) count = 0;
            invalid = false;
            mandelbrotThread(threads, -2, -1, 1, 1, 1, height, 256, nullptr);
            if (invalid) return 1;
            for (int row = 0; row < 1201; ++row)
                if (visits[row] != (row < height ? 1 : 0)) return 1;
            ++cases;
        }
    }
    std::printf("PASS: %d configurations; every valid row visited exactly once, no out-of-range rows.\n", cases);
}
