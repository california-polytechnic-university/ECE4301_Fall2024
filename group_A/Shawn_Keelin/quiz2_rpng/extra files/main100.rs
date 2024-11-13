use rand::Rng; // Import random number generation
use std::time::Instant; // Import timing functionality
use sysinfo::{System}; // Import system info to measure memory usage
use num_primes::Verification; // Import prime verification functions from num-primes
use num_bigint::BigUint; // Import BigUint for large integer handling
use std::f64; // For f64::consts::PI for statistics (std used for standard deviation)

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

// Function to calculate the average of a vector of f64 values
fn average(data: &Vec<f64>) -> f64 {
    let sum: f64 = data.iter().sum();
    sum / data.len() as f64
}

// Function to calculate the standard deviation of a vector of f64 values
fn std_dev(data: &Vec<f64>, avg: f64) -> f64 {
    let variance: f64 = data.iter().map(|&x| (x - avg).powi(2)).sum::<f64>() / data.len() as f64;
    variance.sqrt()
}

fn main() {
    // Initialize system info and timer for measuring memory usage and time
    let mut system = System::new_all(); // Create a new system object
    system.refresh_all(); // Refresh to gather current memory data

    let mut execution_times: Vec<f64> = Vec::new();
    let mut memory_usages: Vec<u64> = Vec::new();

    // Run the program 100 times
    for _ in 0..100 {
        system.refresh_all();
        system.refresh_memory();
        
        let start_time = Instant::now(); // Start timing

        let prime_number = generate_random_prime(); // Generate a random prime number

        let elapsed_time = start_time.elapsed().as_secs_f64(); // Measure elapsed time in seconds

        system.refresh_memory(); // Refresh memory data to get updated usage
        let memory_usage = system.used_memory(); // Get memory usage in KB

        // Store the results
        execution_times.push(elapsed_time);
        memory_usages.push(memory_usage);

        // Optionally, print each run's result (optional for debugging)
        // println!("Run: Prime: {} | Time: {:.4} secs | Memory: {} KB", prime_number, elapsed_time, memory_usage);
    }

    // Perform analysis
    let exec_time_avg = average(&execution_times);
    let exec_time_std = std_dev(&execution_times, exec_time_avg);
    let exec_time_min = execution_times.iter().cloned().fold(f64::INFINITY, f64::min);
    let exec_time_max = execution_times.iter().cloned().fold(f64::NEG_INFINITY, f64::max);

    let memory_usage_avg = average(&memory_usages.iter().map(|&x| x as f64).collect());
    let memory_usage_std = std_dev(&memory_usages.iter().map(|&x| x as f64).collect(), memory_usage_avg);
    let memory_usage_min = memory_usages.iter().cloned().min().unwrap();
    let memory_usage_max = memory_usages.iter().cloned().max().unwrap();

    // Display the analysis results
    println!("Execution Time Analysis (seconds):");
    println!("  Average: {:.4}", exec_time_avg);
    println!("  Minimum: {:.4}", exec_time_min);
    println!("  Maximum: {:.4}", exec_time_max);
    println!("  Standard Deviation: {:.4}\n", exec_time_std);

    println!("Memory Usage Analysis (KB):");
    println!("  Average: {:.2}", memory_usage_avg);
    println!("  Minimum: {}", memory_usage_min);
    println!("  Maximum: {}", memory_usage_max);
    println!("  Standard Deviation: {:.2}", memory_usage_std);

    // Optionally, save to a file
    use std::fs::File;
    use std::io::Write;

    let mut file = File::create("rust_program_analysis.txt").expect("Unable to create file");

    // Write execution time analysis
    writeln!(file, "Execution Time Analysis (seconds):").expect("Unable to write data");
    writeln!(file, "  Average: {:.4}", exec_time_avg).expect("Unable to write data");
    writeln!(file, "  Minimum: {:.4}", exec_time_min).expect("Unable to write data");
    writeln!(file, "  Maximum: {:.4}", exec_time_max).expect("Unable to write data");
    writeln!(file, "  Standard Deviation: {:.4}\n", exec_time_std).expect("Unable to write data");

    // Write memory usage analysis
    writeln!(file, "Memory Usage Analysis (KB):").expect("Unable to write data");
    writeln!(file, "  Average: {:.2}", memory_usage_avg).expect("Unable to write data");
    writeln!(file, "  Minimum: {}", memory_usage_min).expect("Unable to write data");
    writeln!(file, "  Maximum: {}", memory_usage_max).expect("Unable to write data");
    writeln!(file, "  Standard Deviation: {:.2}", memory_usage_std).expect("Unable to write data");
}
