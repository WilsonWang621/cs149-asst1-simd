#include <stdio.h>
#include <thread>
#include <cstdlib>

#include "CycleTimer.h"

typedef struct {
    float x0, x1;
    float y0, y1;
    unsigned int width;
    unsigned int height;
    int maxIterations;
    int* output;
    int threadId;
    int numThreads;
    double elapsedSeconds;
} WorkerArgs;


extern void mandelbrotSerial(
    float x0, float y0, float x1, float y1,
    int width, int height,
    int startRow, int numRows,
    int maxIterations,
    int output[]);


//
// workerThreadStart --
//
// Thread entrypoint.
void workerThreadStart(WorkerArgs * const args) {
    const double startTime = CycleTimer::currentSeconds();

    // Adjacent blocks share a boundary, covering every row exactly once.
    const int startRow = args->height * args->threadId / args->numThreads;
    const int endRow = args->height * (args->threadId + 1) / args->numThreads;
    const int numRows = endRow - startRow;

    mandelbrotSerial(args->x0, args->y0, args->x1, args->y1,
                     args->width, args->height, startRow, numRows,
                     args->maxIterations, args->output);
    const double endTime = CycleTimer::currentSeconds();
    args->elapsedSeconds = endTime - startTime;
}

//
// MandelbrotThread --
//
// Multi-threaded implementation of mandelbrot set image generation.
// Threads of execution are created by spawning std::threads.
void mandelbrotThread(
    int numThreads,
    float x0, float y0, float x1, float y1,
    int width, int height,
    int maxIterations, int output[], double threadSeconds[] = nullptr)
{
    static constexpr int MAX_THREADS = 32;

    if (numThreads < 1 || numThreads > MAX_THREADS)
    {
        fprintf(stderr, "Error: Thread count must be between 1 and %d\n", MAX_THREADS);
        exit(1);
    }

    // Creates thread objects that do not yet represent a thread.
    std::thread workers[MAX_THREADS];
    WorkerArgs args[MAX_THREADS];

    for (int i=0; i<numThreads; i++) {
      
        // TODO FOR CS149 STUDENTS: You may or may not wish to modify
        // the per-thread arguments here.  The code below copies the
        // same arguments for each thread
        args[i].x0 = x0;
        args[i].y0 = y0;
        args[i].x1 = x1;
        args[i].y1 = y1;
        args[i].width = width;
        args[i].height = height;
        args[i].maxIterations = maxIterations;
        args[i].numThreads = numThreads;
        args[i].output = output;
      
        args[i].threadId = i;
    }

    // Spawn the worker threads.  Note that only numThreads-1 std::threads
    // are created and the main application thread is used as a worker
    // as well.
    for (int i=1; i<numThreads; i++) {
        workers[i] = std::thread(workerThreadStart, &args[i]);
    }
    
    workerThreadStart(&args[0]);

    // join worker threads
    for (int i=1; i<numThreads; i++) {
        workers[i].join();
    }

    // Read worker measurements only after every worker has finished.
    if (threadSeconds != nullptr) {
        for (int i = 0; i < numThreads; ++i)
            threadSeconds[i] = args[i].elapsedSeconds;
    }
}

