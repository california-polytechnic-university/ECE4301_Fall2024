use rand::Rng;
use std::fs;
use std::time::{Duration, Instant};

/// Converts a Duration into a human-readable string.
fn pretty_duration(duration: Duration) -> String {
    if duration.as_secs() > 0 {
        format!("{:.3} seconds", duration.as_secs_f64())
    } else if duration.as_millis() > 0 {
        format!("{} milliseconds", duration.as_millis())
    } else {
        format!("{} microseconds", duration.as_micros())
    }
}

/// Reads the process's memory usage in kilobytes by analyzing /proc/self/status.
fn fetch_memory_usage() -> Result<usize, &'static str> {
    let content = fs::read_to_string("/proc/self/status").map_err(|_| "Could not access /proc/self/status")?;

    for line in content.lines() {
        if line.starts_with("VmRSS:") {
            let memory_kb: Vec<&str> = line.split_whitespace().collect();
            return memory_kb.get(1)
                .and_then(|value| value.parse::<usize>().ok())
                .ok_or("Failed to parse VmRSS value");
        }
    }
    Err("VmRSS not found in /proc/self/status")
}

/// Determines whether a number is prime using trial division with optimizations.
fn check_prime(number: u64) -> bool {
    if number <= 1 {
        return false;
    }
    if number == 2 || number == 3 {
        return true;
    }
    if number % 2 == 0 || number % 3 == 0 {
        return false;
    }

    let max_check = (number as f64).sqrt() as u64;
    for i in (5..=max_check).step_by(6) {
        if number % i == 0 || number % (i + 2) == 0 {
            return false;
        }
    }
    true
}
/// Randomly generates a prime number within a specified time limit.
fn find_random_prime(limit: Duration) -> Result<u64, &'static str> {
    let mut rng = rand::thread_rng();
    let start_time = Instant::now();

    while start_time.elapsed() < limit {
        let candidate: u64 = rng.gen_range(3..u64::MAX) | 1; // Ensures the number is odd
        if check_prime(candidate) {
            return Ok(candidate);
        }
    }
    Err("Timeout reached")
}

fn main() {
    println!("Generating Prime Number...");

    // Record the initial memory usage
    let start_memory = fetch_memory_usage().unwrap_or(0);

    // Simulate memory usage with a large vector
    let mut large_data: Vec<u64> = (1..=1_000_000).collect();
    large_data.iter_mut().for_each(|x| *x *= 2); // Modify to ensure memory is used

    // Introduce a slight delay
    std::thread::sleep(Duration::from_millis(100));

    // Set a 30-second timeout for finding a prime number
    let timeout = Duration::from_secs(30);
    let start_time = Instant::now();

    // Attempt to find a random prime within the time limit
    let result = find_random_prime(timeout);
    let elapsed_time = start_time.elapsed();

    // Measure memory usage after the operation
    let end_memory = fetch_memory_usage().unwrap_or(0);

    // Display the results
    match result {
        Ok(prime) => println!("Prime Number Found: {}", prime),
        Err(e) => println!("Prime number generation failed: {}", e),
    }
    println!("Time taken: {}", pretty_duration(elapsed_time));
    println!("Memory Usede: {} KB", end_memory.saturating_sub(start_memory));
