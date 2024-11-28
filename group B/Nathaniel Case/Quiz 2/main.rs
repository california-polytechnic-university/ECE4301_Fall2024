use std::io;

fn is_prime(number: u64) -> bool {
    if number <= 1 {
        return false;
    }
    if number <= 3 {
        return true;
    }
    if number % 2 == 0 || number % 3 == 0 {
        return false;
    }

    let limit = (number as f64).sqrt() as u64 + 1;
    let mut i = 5;
    while i <= limit {
        if number % i == 0 || number % (i + 2) == 0 {
            return false;
        }
        i += 6;
    }
    true
}

fn generate_primes(limit: u64) -> Vec<u64> {
    let mut primes = Vec::new();
    for num in 2..=limit {
        if is_prime(num) {
            primes.push(num);
        }
    }
    primes
}

fn main() {
    println!("Enter the upper limit for generating prime numbers:");

    let mut input = String::new();
    io::stdin().read_line(&mut input).expect("Failed to read input");
    let limit: u64 = input.trim().parse().expect("Please enter a valid number");

    let primes = generate_primes(limit);
    println!("Prime numbers up to {}: {:?}", limit, primes);
}
