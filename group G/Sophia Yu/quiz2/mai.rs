use rand::Rng;



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
    let mut rng = rand::thread_rng();
    let mut random_number: u64 = rng.gen(); // Generates a random u64 number

    // Loop until a prime number is found
    loop {
        random_number = rng.gen(); // Generate a random u64 number
        // println!("Generated number: {}", random_number);
    
        if trial_division(random_number) {
            println!("prime number: {}!", random_number);
            break; // Exit the loop if the number is prime
        } else {
            // println!("{} is not a prime number. Generating another...", random_number);
        }
    }

    println!("\n");

}
