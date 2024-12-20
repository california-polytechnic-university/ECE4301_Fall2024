# Prime Number Generator with Memory Usage Tracking

video: https://youtu.be/Uq7hSaGHIVo

This Rust program generates a random prime number using the **trial division** method and tracks the **memory usage** of the program before and after finding the prime number. The memory usage is retrieved by reading the Linux `/proc/self/status` file.

---

<img width="741" alt="76FF7B14-9A83-4EF9-B03C-44D717DB893C" src="https://github.com/user-attachments/assets/3f496d15-9ea4-494c-9a55-da0414ac12bd">

## How It Works

1. **Get Initial Memory Usage:**
   - The program starts by retrieving the initial memory usage of the process using the `get_memory_usage` function.
   - This function reads the `VmRSS` (Resident Set Size) field from `/proc/self/status`.

2. **Generate a Random Prime Number:**
   - A loop generates random `u64` numbers.
   - Each random number is checked for primality using the `trial_division` function.
   - The loop stops as soon as a prime number is found.

3. **Get Final Memory Usage:**
   - After finding the prime number, the program retrieves the memory usage again.
   - The difference between the initial and final memory usage is calculated and displayed.

4. **Output Results:**
   - The program outputs:
     - The initial memory usage.
     - The generated prime number.
     - The final memory usage.
     - The total change in memory usage (positive or negative).

---

## Code Components

### 1. `get_memory_usage` Function
- **Purpose:** Fetches the current memory usage of the program.
- **How it works:**
  - Reads `/proc/self/status`, a Linux-specific virtual file containing process information.
  - Searches for the line starting with `VmRSS:`.
  - Extracts the memory usage in kilobytes.
- **Error Handling:**
  - Returns a descriptive error if the file cannot be read or `VmRSS` is not found.

### 2. `trial_division` Function
- **Purpose:** Checks whether a given number is prime using the trial division method.
- **How it works:**
  - Handles edge cases for small numbers (`< 2`, `2`, `3`).
  - Skips even numbers to optimize checks.
  - Divides the number by all odd numbers up to its square root to determine if it has factors.

### 3. `main` Function
- **Overview:**
  - Retrieves initial memory usage.
  - Finds a random prime number using a loop and `trial_division`.
  - Retrieves final memory usage.
  - Outputs all relevant data, including the memory usage difference.

---
