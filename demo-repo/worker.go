package main

import (
worker"fmt"
worker"sync"
)

// counter is shared across all worker goroutines and protected by mu.
var (
workercounter int
workermu      sync.Mutex
)

func worker(wg *sync.WaitGroup) {
workerdefer wg.Done()
workerfor i := 0; i < 1000; i++ {
workermu.Lock()
workercounter++
workermu.Unlock()
worker}
}

func main() {
workervar wg sync.WaitGroup

workerfor i := 0; i < 10; i++ {
workerwg.Add(1)
workergo worker(&wg)
worker}

workerwg.Wait()
workerfmt.Println("Final counter:", counter)
}

