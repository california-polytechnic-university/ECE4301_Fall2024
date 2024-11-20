use rand::Rng;
use std::fs;

fn get_memory_usage() -> Result<usize, String> {
    let status = fs::read_to_string("/proc/self/status")
        .map_err(|_| "Failed to read /proc/self/status".to_string())?;

    for line in status.lines() {
        if line.starts_with("VmRSS:") {
            let parts: Vec<&str> = line.split_whitespace().collect();
            if let Some(value) = parts.get(1) {
                return value.parse::<usize>().map_err(|_| "Failed to parse memory usage".to_string());
            }
        }
    }

    Err("VmRSS not found".to_string())
}

fn trial_division(n: u64) -> bool {

    // Handle small cases directly
    if n < 2 {
        return false;
    }
    if n == 2 || n == 3 {
        return true;
    }
    if n % 2 == 0 {
        return false;
    }

    // Initializing with the value 2 from where the number is checked
    let mut i = 3;

    // Computing the square root of the number N
    let k = (n as f64).sqrt().ceil() as u64;

    // While loop till the square root of N
    while i <= k {
        // Check for factors
        if n % i == 0 {
            return false;
        }
        i += 2; // Skip even numbers
    }

    // If none of the numbers is a factor, then it is a prime number
    true
}


fn main() {
    match get_memory_usage() {
        Ok(initial_memory_usage) => {
            println!("Initial memory usage: {} kB", initial_memory_usage);

            let mut rng = rand::thread_rng();
            let mut random_number: u64;

            loop {
                random_number = rng.gen(); // Generate a random u64 number

                if trial_division(random_number) {
                    println!("Prime number found: {}!", random_number);
                    break; // Exit the loop if the number is prime
                }
            }

            // Get memory usage after finding the prime number
            match get_memory_usage() {
                Ok(final_memory_usage) => {
                    println!("Memory usage after finding prime: {} kB", final_memory_usage);
                    println!("total memory usage: {} kb", final_memory_usage-initial_memory_usage);
                }
                Err(e) => {
                    eprintln!("Error fetching memory usage after finding prime: {}", e);
                }
            }
        }
        Err(e) => {
            eprintln!("Error fetching initial memory usage: {}", e);
        }
    }
}
