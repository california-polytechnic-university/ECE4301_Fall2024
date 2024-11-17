use rand::Rng;
use std::time::Instant;
use std::process;
use sysinfo::{ProcessExt, System, SystemExt};

fn get_memory_usage_kb() -> isize {
    let mut system = System::new_all();
    system.refresh_processes();
    let pid = sysinfo::get_current_pid().expect("Failed to get PID");
    let process = system.process(pid).expect("Failed to get process info");
    process.memory() as isize
}

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

    let sqrt_n = (n as f64).sqrt() as u64;
    let mut i = 5;
    
    while i <= sqrt_n {
        if n % i == 0 || n % (i + 2) == 0 {
            return false;
        }
        i += 6;
    }
    true
}

fn generate_random_prime() -> (u64, std::time::Duration) {
    let start_time = Instant::now();
    
    let mut rng = rand::thread_rng();
    let mut attempts = 0;
    let prime = loop {
        attempts += 1;
        // Generate random odd numbers to increase chances of finding a prime
        let candidate: u64 = rng.gen_range(2..u64::MAX) | 1;
        if is_prime(candidate) {
            break candidate;
        }
    };
    
    let duration = start_time.elapsed();
    
    (prime, duration)
}

fn format_duration(duration: std::time::Duration) -> String {
    if duration.as_secs() > 0 {
        format!("{:.2}s", duration.as_secs_f64())
    } else if duration.as_millis() > 0 {
        format!("{}ms", duration.as_millis())
    } else {
        format!("{}µs", duration.as_micros())
    }
}

fn main() {
    println!("Generating a random 64-bit prime number...");

    // Capture initial memory usage
    let initial_memory = get_memory_usage_kb();

    let (prime, duration) = generate_random_prime();

    // Capture final memory usage
    let final_memory = get_memory_usage_kb();

    println!("\nResults:");
    println!("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
    println!("Random prime: {}", prime);
    println!("Execution time: {}", format_duration(duration));
    
    println!("Memory used: {} KB", final_memory - initial_memory);
    println!("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
}
