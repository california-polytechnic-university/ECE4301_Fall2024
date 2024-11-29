use rand::Rng;
use std::time::Instant;
use sysinfo::{System, SystemExt};

fn main() {
    let mut system = System::new_all();

    loop {
        let start = Instant::now();

        // Step 1: Generate a random U64 number
        let number = rand::thread_rng().gen_range(1..u64::MAX);

        // Step 2: Check if the number is prime using trial division
        if trial_division(number) {
            // Measure execution time
            let duration = start.elapsed();
            let duration_secs = duration.as_secs_f64(); // Convert to seconds as a floating-point number

            // Round to two decimal places
            let rounded_duration = format!("{:.2}", duration_secs);

            // Update system information to get memory usage
            system.refresh_memory();
            let memory_used = system.used_memory(); // Memory used in KB

            // Display results only if the number is prime
            println!("Prime Number: {}", number);
            println!("Execution Time: {} seconds", rounded_duration);
            println!("Memory Usage: {} KB", memory_used);
        }
    }
}

// Function to check if a number is prime using Trial Division
fn trial_division(n: u64) -> bool {
    if n <= 1 {
        return false;
    }
    if n <= 3 {
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

