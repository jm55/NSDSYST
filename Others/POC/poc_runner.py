import random
import os
import time
import image_poc as poc

def getCPUCount():
    return int(os.cpu_count())

def main():
    print("Image POC Runner")
    print("CPU Count:", os.cpu_count()/2)
    input_folder = "test_images"
    output_folder = poc.create_folder(input_folder)
    filenames = poc.get_filenames(input_folder)
    
    params = []
    times = []

    for c in range(1, getCPUCount()+1):
        params.append([random.randint(0,100),random.randint(0,100),random.randint(0,100),c])
    print("Benchmarking...")
    
    #Prepare workers
    for c in range(1, os.cpu_count()+1):
        params.append([random.randint(0,100),random.randint(0,100),random.randint(0,100), c])
    
    #Run each worker one at a time
    for p in params:
        start = time.time()
        poc.coordinator(input_folder, filenames, output_folder, p[0], p[1], p[2], p[3])
        end = time.time()
        print(f"Threads: {p[3]} Runtime: {end-start:.2f}s ({(end-start)/len(filenames):.2f}s/image)")
        times.append([p[3], end-start, (end-start)/len(filenames)])
    print("\nBenchmark Complete!")

    #Results
    print("Thread, Time, Time/Image")
    for t in times:
        print(f"{t[0]}, {t[1]}, {t[2]}")

    with open('benchmark.csv', 'w') as f:
        print("Thread, Time, Time/Image", file=f)
        for t in times:
            print(f"{t[0]:.8f}, {t[1]:.8f}, {t[2]:.8f}", file=f)

if __name__ == "__main__":
    main()
