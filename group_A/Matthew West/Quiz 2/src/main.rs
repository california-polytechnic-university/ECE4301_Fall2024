use rand::Rng;
use std::time::Instant;
use windows::Win32::System::SystemInformation::{GlobalMemoryStatus, MEMORYSTATUS};

fn fermat_primality_test(n: u128, iterations: u16) -> bool {
    // Handle small cases for efficiency
    if n < 4 {
        return n == 2 || n == 3;
    }
    
    let mut rng = rand::thread_rng();
    
    for _ in 0..iterations {
        // Generate a random integer 'a' in the range [2, n-2]
        let a = rng.gen_range(2..n-1);
        
        // If a^(n-1) % n is not 1, then n is composite
        if mod_exp(a, n - 1, n) != 1 {
            return false;
        }
    }
    
    // Probably prime if it passes all iterations
    true
}

// Helper function to calculate (base^exp) % modulus efficiently
fn mod_exp(mut base: u128, mut exp: u128, modulus: u128) -> u128 {
    let mut result = 1;
    base = base % modulus;
    while exp > 0 {
        if exp % 2 == 1 {
            result = (result * base) % modulus;
        }
        exp >>= 1;
        base = (base * base) % modulus;
    }
    result
}

fn is_prime(number: u128, iterations: u16) -> bool {
    // Preliminary screening with Fermat's primality test
    if !fermat_primality_test(number, iterations) {
        return false;
    }

    if number <= 1 {
        return false;
    }
    if number <= 3 {
        return true;
    }
    if number % 2 == 0 || number % 3 == 0 {
        return false;
    }

    let limit = (number as f64).sqrt() as u128 + 1;
    let mut i: u128 = 5;
    while i <= limit {
        if number % i == 0 || number % (i + 2) == 0 {
            return false;
        }
        i += 6;
    }
    true
}

// Get memory usage statistics
fn print_mem_stats() {
    let mut mem_status = MEMORYSTATUS::default();
    mem_status.dwLength = std::mem::size_of::<MEMORYSTATUS>() as u32;
    
    unsafe {
        GlobalMemoryStatus(&mut mem_status);
    }
    
    println!("Total memory: {} KB", mem_status.dwTotalPhys / 1024);
    println!("Used memory: {} KB", (mem_status.dwTotalPhys - mem_status.dwAvailPhys) / 1024);
}

fn main() {
    loop {
        // Initialize the random number generator
        let mut rng = rand::thread_rng();
        let iterations: u16 = 100;

        // Take input for gen_selector
        let mut gen_selector = String::new();
        println!("Enter 0 for probable primes, 1 for confirmed primes: ");
        std::io::stdin().read_line(&mut gen_selector).expect("Failed to read line");
        let gen_selector: bool = match gen_selector.trim() {
            "0" => false,
            "1" => true,
            _ => return
        };

        if gen_selector {
            println!("Generating confirmed primes...");
        } else {
            println!("Generating probable primes...");
        }
        
        let mut test_number: u128 = rng.gen_range(2..2u128.pow(64));

        // Start the timer
        let start_time = Instant::now();

        // Generate a probable or confirmed prime number based on the user's choice
        if gen_selector {
            // Generate a confirmed prime number
            while !{ is_prime(test_number, iterations) } {
                test_number += 1;
            }
            println!("{} is prime.", test_number);
        } else {
            // Generate a probable prime number
            while !{ fermat_primality_test(test_number, iterations) } {
                test_number += 1;
            } 
            println!("{} is probably prime.", test_number);
        }

        // Stop the timer
        let duration = start_time.elapsed();
        println!("Time taken for execution: {:?}", duration);
        print_mem_stats();
        println!();
    }
}
