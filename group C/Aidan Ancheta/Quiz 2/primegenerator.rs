use std::time::Instant;
use sysinfo::{System, SystemExt, ProcessExt, Pid, PidExt};

/// Checks if a number is prime
fn is_prime(n: u64) -> bool {
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

fn generate_primes(limit: u64) {
    let mut primes = vec![];
    let start = Instant::now();
    let mut system = System::new_all();

    for num in 2..=limit {
        if is_prime(num) {
            primes.push(num);

            // Debug output: Print progress every 1,000 primes found
            if primes.len() % 1000 == 0 {
                println!("Found {} primes so far...", primes.len());
            }
        }
    }

    // Capture execution time and memory usage
    let duration = start.elapsed();
    let pid = Pid::from(std::process::id() as usize);  // Adjusted pid line
    system.refresh_processes();

    if let Some(proc) = system.process(pid) {
        let memory_usage = proc.memory();
        
        // Display results
        for prime in primes {
            println!("Prime: {}", prime);
        }
        println!("\nExecution Time: {:?}", duration);
        println!("Memory Usage: {} KB", memory_usage);
    } else {
        println!("Could not retrieve memory usage information.");
    }
}


    // Capture execution time and memory usage
    let duration = start.elapsed();
    let pid = Pid::from(std::process::id() as usize);  // Adjusted pid line
    system.refresh_processes();

    if let Some(proc) = system.process(pid) {
        let memory_usage = proc.memory();
        
        // Display results
        for prime in primes {
            println!("Prime: {}", prime);
        }
        println!("\nExecution Time: {:?}", duration);
        println!("Memory Usage: {} KB", memory_usage);
    } else {
        println!("Could not retrieve memory usage information.");
    }
}

fn main() {
    // Set a reasonable limit for demonstration purposes
    let limit = 100_000;
    generate_primes(limit);
}
