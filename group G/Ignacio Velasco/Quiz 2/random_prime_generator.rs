use rand::Rng;
use std::fs;
use std::time::{Instant, Duration};

/// Reads the memory usage (VmRSS) of the current process from /proc/self/statu>
fn get_memory_usage() -> Result<usize, String> {
    let status = fs::read_to_string("/proc/self/status")
        .map_err(|_| "Failed to read /proc/self/status".to_string())?;

    for line in status.lines() {
        if line.starts_with("VmRSS:") {
            let parts: Vec<&str> = line.split_whitespace().collect();
            if let Some(value) = parts.get(1) {
                return value.parse().map_err(|_| "Failed to parse memory usage">
            }
        }
    }
    Err("VmRSS not found".to_string())
}

/// Returns true if the number is prime using an optimized method.
fn is_prime(n: u64) -> bool {
    if n <= 1 {
        return false;
    }
    if n == 2 || n == 3 {
        return true;
    }
    if n % 2 == 0 || n % 3 == 0 {return false;
    }

    let limit = (n as f64).sqrt() as u64;
    (5..=limit).step_by(6).any(|i| n % i == 0 || n % (i + 2) == 0)
}

/// Generates a random prime number within u64::MAX, respecting the timeout lim>
fn generate_random_prime(timeout: Duration) -> Result<u64, String> {
let mut rng = rand::thread_rng();

    while Instant::now().elapsed() < timeout {
        let candidate: u64 = rng.gen_range(2..u64::MAX) | 1; // Ensuring it's odd
        if is_prime(candidate) {
            return Ok(candidate);
        }
    }

    Err("Timeout: No prime found within the given time".to_string())
}

/// Formats a Duration into a readable string.
fn format_duration(duration: Duration) -> String {
    if duration.as_secs() > 0 {
        format!("{:.2}s", duration.as_secs_f64())
    } else if duration.as_millis() > 0 {format!("{}ms", duration.as_millis())
    } else {
        format!("{}µs", duration.as_micros())
    }
}

fn main() {
    println!("\nStarting prime number generation process: ");

    // Record initial memory usage
    let initial_memory = get_memory_usage().unwrap_or(0);

    // Simulate some memory usage
    let _simulated_load: Vec<u64> = (0..1_000_000).collect();

    // Introduce a small delay to simulate real-world behavior
    std::thread::sleep(Duration::from_millis(100));

    // Generate a random prime with a timeout of 30 seconds
    let timeout = Duration::from_secs(30);
    let start_time = Instant::now();  // Start time in the main function

    let (prime, duration) = match generate_random_prime(timeout) {
        Ok(prime_number) => (Some(prime_number), start_time.elapsed()),Err(e) => {
            println!("{}", e);
            (None, start_time.elapsed())
        }
    };

    // Calculate final memory usage
    let final_memory = get_memory_usage().unwrap_or(0);

    // Print results
    match prime {
        Some(p) => println!("\nRandom prime found:  {}", p),
        None => println!("No prime found within the time limit."),
    }
    println!("Execution time:      {}", format_duration(duration));
    println!("Memory used:         {} KB", final_memory - initial_memory);
    println!("\n");
}
