use std::io;
use rand::Rng;
use num::integer::Roots;
use std::time::Instant;
use jemalloc_ctl::{stats, epoch};

#[global_allocator]
static ALLOC: jemallocator::Jemalloc = jemallocator::Jemalloc;

fn main() {
    println!("Enter the limit:");

    let mut input_str = String::new();

    io::stdin()
        .read_line(&mut input_str)
        .expect("Failed to read line");

    let x: u32 = input_str.trim().parse().expect("Input not an integer");

    sieve(x);
}

fn sieve(limit: u32) {
    let e = epoch::mib().unwrap();
    let allocated = stats::allocated::mib().unwrap();

    let mut nums = vec![true; limit as usize];

    let start = Instant::now();
    for i in 2..(limit.sqrt()+1) {
        if nums[i as usize] {
            for j in (i*i..limit).step_by(i as usize) {
                nums[j as usize] = false;
            }
        }
    }
    let duration = start.elapsed();

    e.advance().unwrap();

    let mut primes = Vec::new();
    for i in 2..nums.len() {
        if nums[i] {
            primes.push(i);
        }
    }

    let mut rng = rand::thread_rng();
    let chosen = rng.gen_range(0..primes.len());

    println!("Primes up to {} found in {:?} using {} bytes. Random prime in range: {}", limit, duration, allocated.read().unwrap(), primes[chosen]);
}