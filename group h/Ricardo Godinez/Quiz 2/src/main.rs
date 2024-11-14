use std::time::Instant;
use sysinfo::{System, SystemExt, ProcessExt};

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
    let mut i = 5;
    while i * i <= n {
        if n % i == 0 || n % (i + 2) == 0 {
            return false;
        }
        i += 6;
    }
    true
}

fn main() {
    let start = Instant::now();
    let mut sys = System::new_all();

    println!("Generating prime numbers in u64 range...");

    let mut count = 0;
    for num in 2..u64::MAX {
        if is_prime(num) {
            println!("Prime Number: {}", num);
            count += 1;
        }

        if count >= 10 { // stop after finding 10 primes, or adjust as desired
            break;
        }
    }

    let duration = start.elapsed();
    sys.refresh_all();
    
    let process = sys.process(sysinfo::get_current_pid().unwrap()).unwrap();
    let memory_usage = process.memory();

    println!("Execution Time: {:?}", duration);
    println!("Memory Usage: {} KB", memory_usage);
}
