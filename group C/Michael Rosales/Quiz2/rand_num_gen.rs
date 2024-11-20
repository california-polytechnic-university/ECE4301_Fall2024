
use rand::Rng;
use std::time::{Instant, Duration};
use std::fs;

fn get_memory_usage_kb() -> usize {
    let status = fs::read_to_string("/proc/self/status").expect("Failed to read /proc/self/status");
    for line in status.lines() {
        if line.starts_with("VmRSS:") {
            let parts: Vec<&str> = line.split_whitespace().collect();
            if let Some(value) = parts.get(1) {
                return value.parse().unwrap_or(0);
            }
        }
    }
    0
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

fn generate_random_prime() -> (Option<u64>, std::time::Duration) {
    let start_time = Instant::now();
    let max_duration = Duration::from_secs(30); // maximum search duration of 30 sec

    let mut rng = rand::thread_rng();
    let prime = loop {
        let candidate: u64 = (rng.gen_range(0..u64::MAX) | 1) | (1 << 63); // Ensure 64 bits
        if is_prime(candidate) {
            break Some(candidate);
        }
        if start_time.elapsed() > max_duration {
            println!("Timeout reached, stopping prime search.");
            break None;
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
    println!("\nGenerating a random 64-bit prime number...");

    // Capture initial memory usage
    let initial_memory = get_memory_usage_kb();

    let mut vec = Vec::with_capacity(1_000_000);
    for i in 0..1_000_000 {
        vec.push(i);
    }

    std::thread::sleep(Duration::from_millis(100));

    let (prime, duration) = generate_random_prime();

    // Capture final memory usage
    let final_memory = get_memory_usage_kb();

    println!("\n");
    println!("=======================================");
    match prime {
        Some(p) => println!("Random prime:         {}", p),
        None => println!("Failed to find a prime within the time limit."),
    }
    println!("Execution time:    {}", format_duration(duration));
    println!("Memory used:       {} KB", final_memory - initial_memory);
    println!("\n");
}

