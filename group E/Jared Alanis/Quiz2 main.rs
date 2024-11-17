use rand::Rng;
use std::{thread, time::Duration, time::Instant};
use sys_info;

/// Function to perform modular exponentiation
/// Computes (base^exp) % modulus using efficient method
fn mod_exp(base: u64, exp: u64, modulus: u64) -> u64 {
    let mut result = 1u128;
    let mut base = base as u128 % modulus as u128;
    let mut exp = exp;

    while exp > 0 {
        if exp % 2 == 1 {
            result = (result * base) % modulus as u128;
        }
        exp >>= 1;
        base = (base * base) % modulus as u128;
    }
    result as u64
}

/// Miller-Rabin Primality Test
/// This function returns true if `n` is likely prime, false if it's composite.
/// `k` is the number of rounds of testing for accuracy.
fn is_prime(n: u64, k: u32) -> bool {
    if n <= 1 || n == 4 {
        return false;
    }
    if n <= 3 {
        return true;
    }

    // Find `d` such that n - 1 = d * 2^r where `d` is odd
    let mut d = n - 1;
    let mut r = 0;
    while d % 2 == 0 {
        d /= 2;
        r += 1;
    }

    // Witness loop
    'outer: for _ in 0..k {
        // Choose a random base `a` in the range [2, n - 2]
        let a = 2 + rand::thread_rng().gen_range(0..(n - 4));
        let mut x = mod_exp(a, d, n);

        if x == 1 || x == n - 1 {
            continue;
        }

        for _ in 0..(r - 1) {
            x = (x as u128 * x as u128 % n as u128) as u64;
            if x == n - 1 {
                continue 'outer;
            }
        }
        return false; // Composite
    }
    true // Likely prime
}

fn main() {
    loop {
        // Start timing
        let start = Instant::now();

        // Generate random number in a suitable range for U64
        let mut rng = rand::thread_rng();
        let candidate: u64 = rng.gen_range(1_000_000_000..u64::MAX);

        // Check if the number is prime
        if is_prime(candidate, 5) {
            // Stop timing
            let duration = start.elapsed();

            // Get memory usage
            let mem_info = sys_info::mem_info().unwrap();
            let used_memory = (mem_info.total - mem_info.free) / 1024; // KB to MB conversion

            // Display output
            println!("Prime Number: {}", candidate);
            println!("Execution Time: {:?}", duration);
            println!("Memory Usage: {} MB", used_memory);
            println!(); // Add a single blank line for separation

            // Wait for 1 second before generating the next prime
            thread::sleep(Duration::from_secs(1));
        }
    }
}
