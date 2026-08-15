package main

import (
	"fmt"
	"sync"
)

// counter is shared across all worker goroutines and protected by mu.
var (
	counter int
	mu      sync.Mutex
)

func worker(wg *sync.WaitGroup) {
	defer wg.Done()
	for i := 0; i < 1000; i++ {
		mu.Lock()
		counter++
		mu.Unlock()
	}
}

func main() {
	var wg sync.WaitGroup

	for i := 0; i < 10; i++ {
		wg.Add(1)
		go worker(&wg)
	}

	wg.Wait()
	fmt.Println("Final counter:", counter)
}
