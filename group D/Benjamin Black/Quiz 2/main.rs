use rand::Rng;
use std::time::Instant;
use sys_info;

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
    let limit = (n as f64).sqrt() as u64;
    for i in 5..=limit {
        if n % i == 0 {
            return false;
        }
    }
    true
}

fn generate_random_prime() -> u64 {
    let mut rng = rand::thread_rng();
    loop {
        let number: u64 = rng.gen_range(2..=u64::MAX); // Generate a random number
        if is_prime(number) {
            return number;
        }
    }
}

fn main() {
    for i in 1..=5 {
        // Measure execution time
        let start_time = Instant::now();
        
        let prime = generate_random_prime();
        
        let duration = start_time.elapsed();
        
        // Fetch and format memory usage
        let memory_usage = match sys_info::mem_info() {
            Ok(mem) => format!("{} MB free", mem.free / 1024),
            Err(e) => format!("Failed to get memory info: {}", e),
        };

        // Output all information on a single line
        println!("#{} Prime Number: {}, #2 Execution Time: {:?}, #3 Memory Usage: {}", 
                 i, prime, duration, memory_usage);
    }
}
