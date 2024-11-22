use std::time::Instant;
use sysinfo::{System, SystemExt}; // For memory usage

fn is_prime(n: u64) -> bool {
    if n < 2 {
        return false;
    }
    if n == 2 || n == 3 {
        return true;
    }
    if n % 2 == 0 || n % 3 == 0 {
        return false;
    }
    let mut i = 5;
    while i * i <= n {
        if n % i == 0 || n % (i + 2) == 0 {
            return false;
        }
        i += 6;
    }
    true
}

// Generate a random prime number below the given maximum
fn generate_random_prime(max: u64) -> u64 {
    let mut rng = rand::thread_rng(); // Random number generator
    loop {
        let candidate: u64 = rand::Rng::gen_range(&mut rng, 2..max);
        if is_prime(candidate) {
            return candidate;
        }
    }
}

fn main() {
    let mut system = System::new_all(); // Make the system object mutable
    system.refresh_all(); // Refresh system information
    let memory_before = system.used_memory();

    let start = Instant::now();
    let max_value: u64 = u64::MAX / 100_000; // Set an upper limit for demonstration
    let prime = generate_random_prime(max_value);
    let duration = start.elapsed();

    system.refresh_all(); // Refresh system info after operation
    let memory_after = system.used_memory();

    println!("Random Prime Number: {}", prime);
    println!("Execution Time: {:.2?}", duration);
    println!("Memory Usage: {} KB", (memory_after - memory_before));
}
