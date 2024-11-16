use num_bigint::{BigUint, ToBigUint};
use num_traits::{One, Zero};
use num_integer::Integer;
use rand::Rng;
use std::time::Instant;
use sysinfo::{ProcessExt, System, SystemExt};

fn is_prime(n: &BigUint, k: u32) -> bool {
    if *n < BigUint::from(2u32) {
        return false;
    }
    if *n == BigUint::from(2u32) || *n == BigUint::from(3u32) {
        return true;
    }
    if n.is_even() {
        return false;
    }

    let mut d = n - BigUint::one();
    let mut r = 0;
    while d.is_even() {
        d >>= 1;
        r += 1;
    }

    let mut rng = rand::thread_rng();
    for _ in 0..k {
        let a = generate_random_biguint_range(&BigUint::from(2u32), &(n - BigUint::from(2u32)));
        let mut x = a.modpow(&d, n);
        if x == BigUint::one() || x == n - BigUint::one() {
            continue;
        }
        let mut composite = true;
        for _ in 0..(r - 1) {
            x = x.modpow(&BigUint::from(2u32), n);
            if x == n - BigUint::one() {
                composite = false;
                break;
            }
        }
        if composite {
            return false;
        }
    }
    true
}

fn generate_random_biguint_range(lower: &BigUint, upper: &BigUint) -> BigUint {
    let mut rng = rand::thread_rng();
    let range = upper - lower + BigUint::one();
    let bits = range.bits();
    loop {
        let mut random_bytes = vec![0u8; ((bits + 7) / 8) as usize];
        rng.fill(&mut random_bytes[..]);
        let num = BigUint::from_bytes_be(&random_bytes);
        if &num < &range {
            return lower + num;
        }
    }
}

fn main() {
    let start = Instant::now();

    let mut system = System::new_all();
    system.refresh_processes();

    let pid = sysinfo::get_current_pid().expect("Failed to get PID");
    let process = system.process(pid).expect("Failed to get process info");

    // Capture initial memory usage
    let initial_memory = process.memory();

    let mut rng = rand::thread_rng();
    let mut large_memory_allocation = Vec::new();

    // Generate and store multiple BigUint values to increase memory usage
    for _ in 0..100_000 {
        let random_u64 = rng.gen::<u64>();
        let big_uint = BigUint::from(random_u64);
        large_memory_allocation.push(big_uint);
    }

    // Generate a random BigUint in the range [0, 2^64 - 1] and find the next prime
    let random_u64 = rng.gen::<u64>();
    let mut candidate = BigUint::from(random_u64);

    if candidate < BigUint::from(2u32) {
        candidate = BigUint::from(2u32);
    }

    let mut attempts = 0u64;
    let max_attempts = 1_000_000u64;

    while !is_prime(&candidate, 20) {
        candidate += BigUint::one();
        attempts += 1;
        if attempts >= max_attempts {
            println!("Could not find a prime number within {} attempts.", max_attempts);
            break;
        }
        if candidate.is_even() {
            candidate += BigUint::one();
        }
    }

    // Refresh system info to get updated memory usage
    system.refresh_processes();
    let updated_process = system.process(pid).expect("Failed to get process info");

    // Capture memory usage after execution
    let final_memory = updated_process.memory();

    // Calculate the difference in memory usage
    let memory_difference = final_memory as isize - initial_memory as isize;

    let duration = start.elapsed();
    if attempts < max_attempts {
        println!("Random prime number: {}", candidate);
    }
    println!("Execution time: {:?}", duration);
    println!("Memory usage difference: {} KB", memory_difference);
}
