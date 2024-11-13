use rand::Rng; // Import random number generation
use std::time::Instant; // Import timing functionality
use sysinfo::{System}; // Import system info to measure memory usage
use num_primes::Verification; // Import prime verification functions from num-primes
use num_bigint::BigUint; // Import BigUint for large integer handling

// Function to generate a random prime number between 0 and (2^64)-1
fn generate_random_prime() -> u64 {
    let mut rng = rand::thread_rng(); // Create a random number generator
    loop {
        let candidate = rng.gen_range(0..u64::MAX); // Generate a random number in the range
        let candidate_biguint = BigUint::from(candidate); // Convert u64 to BigUint
        if Verification::is_prime(&candidate_biguint) { // Check if the number is prime using num-primes
            return candidate; // Return the number if it's prime
        }
    }
}

fn main() {
    // Initialize system info and timer for measuring memory usage and time
    let mut system = System::new_all(); // Create a new system object
    system.refresh_all(); // Refresh to gather current memory data

    let start_time = Instant::now(); // Start timing

    let prime_number = generate_random_prime(); // Generate a random prime number

    let elapsed_time = start_time.elapsed(); // Measure elapsed time

    system.refresh_memory(); // Refresh memory data to get updated usage

    // Display the generated prime number, execution time, and memory usage
    println!("Generated prime number: {}", prime_number);
    println!("Execution time: {:.2?}", elapsed_time);
    println!("Memory used: {} KB", system.used_memory()); // Display used memory in KB
}