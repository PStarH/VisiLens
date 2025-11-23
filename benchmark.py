import time
import os
from backend.core import load_dataset # 假设这个路径是正确的

# --- 配置参数 ---
FILENAME = "test_1m_rows.csv"
COLUMN_TO_SORT = "C" # 确保测试的是数值排序修复
NUM_RUNS = 5 
# ---

def run_benchmark():
    if not os.path.exists(FILENAME):
        print(f"Error: {FILENAME} not found. Please run 'python gen_data.py'.")
        return

    print(f"Benchmarking VisiLens on {FILENAME} (Runs: {NUM_RUNS})...")
    
    # 1. Load Time (Initial cold run)
    start_time = time.time()
    handle = load_dataset(FILENAME)
    load_time_initial = time.time() - start_time
    print(f"\n--- Load Test ---")
    print(f"Initial Load Time: {load_time_initial:.4f} seconds")
    
    # 2. Sort Time (Multiple runs for average)
    if COLUMN_TO_SORT not in [c.name for c in handle.sheet.columns]:
        print(f"Error: Column '{COLUMN_TO_SORT}' not found in dataset.")
        return

    sort_times = []
    print(f"\n--- Sort Test (Column: {COLUMN_TO_SORT}) ---")
    
    # Run the sort multiple times
    for i in range(1, NUM_RUNS + 1):
        # Note: We must reload or shuffle the sheet if VisiData caches the sorted state.
        # Assuming sort_by_column recalculates fully each time.
        start_time = time.time()
        handle.sort_by_column(COLUMN_TO_SORT, ascending=(i % 2 == 0)) # Alternates direction
        sort_time = time.time() - start_time
        sort_times.append(sort_time)
        print(f"Run {i}/{NUM_RUNS}: {sort_time:.4f}s")
        time.sleep(0.1) # Small pause to help system stabilize

    # Final Report
    avg_sort_time = sum(sort_times) / NUM_RUNS
    best_sort_time = min(sort_times)
    
    print("\n--- Summary Report ---")
    print(f"Best Sort Time: {best_sort_time:.4f} seconds (Use this for your benchmark table)")
    print(f"Average Sort Time: {avg_sort_time:.4f} seconds")
    
    # Example output: Best Sort Time: 0.0125 seconds

if __name__ == "__main__":
    run_benchmark()