use std::time::{Instant, Duration};
use sysinfo::{System}; // Removed Process
use std::io::{self, Write};

fn get_memory_usage_kb(system: &mut System) -> isize {
    system.refresh_memory(); // Refresh only memory information

    let pid = sysinfo::get_current_pid().expect("Failed to get PID");
    if let Some(process) = system.process(pid) {
        process.memory() as isize
    } else {
        0 // Return 0 if no process is found
    }
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

fn format_duration(duration: Duration) -> String {
    if duration.as_secs() > 0 {
        format!("{:.2}s", duration.as_secs_f64())
    } else if duration.as_millis() > 0 {
        format!("{}ms", duration.as_millis())
    } else if duration.as_micros() > 0 {
        format!("{}Âµs", duration.as_micros())
    } else {
        format!("{}ns", duration.as_nanos())
    }
}

fn main() {
    // Prompt user for limit
    print!("Enter the limit for generating prime numbers: ");
    io::stdout().flush().expect("Failed to flush stdout");

    let mut input = String::new();
    io::stdin().read_line(&mut input).expect("Failed to read input");
    let limit: u64 = input.trim().parse().expect("Please enter a valid number");

    println!("\nGenerating prime numbers up to {} with individual timings and memory usage...", limit);
    println!("Prime Number | Time Execution | Memory Usage (KB)");
    println!("----------------------------------------------------------------------------------------------------------------------------");
  
    let mut system = System::new_all();  // Initialize system with all data
    let mut start_time = Instant::now();

    for num in 0..=limit {
        if is_prime(num) {
            let elapsed_time = start_time.elapsed();
            let memory_usage = get_memory_usage_kb(&mut system);
            println!("{:<12} | {:<15} | {} KB", num, format_duration(elapsed_time), memory_usage);

            // Reset start time for the next prime check
            start_time = Instant::now();
        }
    }

    println!("----------------------------------------------------------------------------------------------------------------------------");
}
