use rand::Rng;
use std::time::Instant;
use std::process;

#[cfg(target_os = "linux")]
fn get_memory_usage() -> u64 {
    use std::fs::File;
    use std::io::Read;
    
    let mut status = String::new();
    if let Ok(mut file) = File::open(format!("/proc/{}/status", process::id())) {
        file.read_to_string(&mut status).unwrap_or(0);
        for line in status.lines() {
            if line.starts_with("VmRSS:") {
                return line.split_whitespace()
                    .nth(1)
                    .and_then(|x| x.parse::<u64>().ok())
                    .unwrap_or(0);
            }
        }
    }
    0
}

#[cfg(not(target_os = "linux"))]
fn get_memory_usage() -> u64 {
    0 // Return 0 for non-Linux systems as a fallback
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

fn generate_random_prime() -> (u64, std::time::Duration, u64) {
    let start_time = Instant::now();
    let initial_memory = get_memory_usage();
    
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
    let final_memory = get_memory_usage();
    let memory_used = final_memory.saturating_sub(initial_memory);
    
    (prime, duration, memory_used)
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

fn format_memory(kb: u64) -> String {
    if kb >= 1024 * 1024 {
        format!("{:.2} GB", kb as f64 / (1024.0 * 1024.0))
    } else if kb >= 1024 {
        format!("{:.2} MB", kb as f64 / 1024.0)
    } else {
        format!("{} KB", kb)
    }
}

fn main() {
    println!("Generating a random 64-bit prime number...");
    
    let (prime, duration, memory_used) = generate_random_prime();
    
    println!("\nResults:");
    println!("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
    println!("Random prime: {}", prime);
    println!("Execution time: {}", format_duration(duration));
    
    if memory_used > 0 {
        println!("Memory usage: {}", format_memory(memory_used));
    } else {
        println!("Memory usage: Not available (non-Linux system)");
    }
    println!("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
}