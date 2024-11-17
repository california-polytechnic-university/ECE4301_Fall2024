use rand::Rng;
use std::fs::File;
use std::io::Read;
use std::time::Instant;

fn is_prime(n: u64) -> bool {
    if n <= 1 {
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

fn memory_usage_kb() -> u64 {
    let mut status = String::new();
    File::open("/proc/self/status")
        .expect("Unable to open /proc/self/status")
        .read_to_string(&mut status)
        .expect("Unable to read /proc/self/status");

    status
        .lines()
        .find(|line| line.starts_with("VmRSS:"))
        .and_then(|line| {
            line.split_whitespace()
                .nth(1) // Get the memory value
                .and_then(|val| val.parse::<u64>().ok())
        })
        .unwrap_or(0)
}

fn main() {
    let start_time = Instant::now();

    let mut rng = rand::thread_rng();

    let prime = loop {
        let candidate = rng.gen_range(1 << 63..u64::MAX);
        if is_prime(candidate) {
            break candidate;
        }
    };

    let execution_time = start_time.elapsed();
    let memory_used = memory_usage_kb();

    println!("Generated 64-bit Prime Number: {}", prime);
    println!("Execution Time: {:.2?}", execution_time);
    println!("Memory Usage: {} KB", memory_used);

    println!("\nPress Enter to exit.");
    let mut input = String::new();
    std::io::stdin().read_line(&mut input).unwrap();
}