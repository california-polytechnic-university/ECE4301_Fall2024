use rand::Rng; // Import random number generation
use std::time::Instant; // Import timing functionality
use sysinfo::{System}; // Import system info to measure memory usage

// Helper function to check if a number is prime
fn is_prime(n: u64) -> bool {
    if n <= 1 {
        return false; // Numbers less than or equal to 1 are not prime
    }
    if n <= 3 {
        return true; // 2 and 3 are prime numbers
    }
    if n % 2 == 0 || n % 3 == 0 {
        return false; // Exclude multiples of 2 and 3
    }
    let mut i = 5;
    while i * i <= n {
        if n % i == 0 || n % (i + 2) == 0 {
            return false; // If divisible by any number up to √n, it's not prime
        }
        i += 6;
    }
    true
}

// Function to generate a random prime number between 0 and (2^64)-1
fn generate_random_prime() -> u64 {
    let mut rng = rand::thread_rng(); // Create a random number generator
    loop {
        let candidate = rng.gen_range(0..u64::MAX); // Generate a random number in the range
        if is_prime(candidate) { // Check if the number is prime
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
    println!("Memory used: {}/{} MB", system.used_memory()/1000000,system.total_memory()/1000000); // Display used memory in MB
}