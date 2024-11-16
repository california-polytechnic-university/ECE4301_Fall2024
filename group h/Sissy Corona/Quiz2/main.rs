use std::time::Instant;
use std::io;
use jemallocator::Jemalloc;
use std::mem;

#[global_allocator]
static GLOBAL: Jemalloc = Jemalloc;

// Modular exponentiation function to prevent overflow
fn mod_exp(mut base: u64, mut exp: u64, modulus: u64) -> u64 {
    let mut result: u64 = 1;
    base = base % modulus;
    while exp > 0 {
        if exp % 2 == 1 {
            result = result.wrapping_mul(base) % modulus;
        }
        exp >>= 1;
        base = base.wrapping_mul(base) % modulus;
    }
    result
}

// Fermat primality test function
fn is_prime_fermat(p: u64, a: u64) -> bool {
    if p <= 1 {
        return false;
    }
    if a >= p || a <= 1 {
        return false;
    }
    // Fermat's little theorem: a^(p-1) % p == 1 if p is prime
    mod_exp(a, p - 1, p) == 1
}

fn main() {
    // Prompt user input for `a` and `p`
    println!("Enter a number `p` to test for primality:");
    let mut input_p = String::new();
    io::stdin().read_line(&mut input_p).expect("Failed to read line");
    let p: u64 = input_p.trim().parse().expect("Please enter a valid integer");

    println!("Enter a base `a` for Fermat test (1 < a < p):");
    let mut input_a = String::new();
    io::stdin().read_line(&mut input_a).expect("Failed to read line");
    let a: u64 = input_a.trim().parse().expect("Please enter a valid integer");

    // Start timing execution
    let start_time = Instant::now();

    // Check if `p` is prime
    let is_prime = is_prime_fermat(p, a);

    // Measure execution time
    let duration = start_time.elapsed();

    // Display results
    if is_prime {
        println!("The number {} is prime according to the Fermat test.", p);
    } else {
        println!("The number {} is composite according to the Fermat test.", p);
    }
    println!("Execution time: {:?}", duration);

    let memory_usage = jemallocator::usable_size(&p) + jemallocator::usable_size(&a);
    let memory_usage_in_mb = memory_usage as f64 / (1024.0 * 1024.0); // Convert bytes to MB
    println!("Memory used: {:.2} MB", memory_usage_in_mb);

}
