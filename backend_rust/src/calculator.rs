pub fn calculate(a: f64, b: f64, operator: &str) -> String {
    match operator {
        "+" => (a + b).to_string(),
        "-" => (a - b).to_string(),
        "*" => (a * b).to_string(),
        "/" => if b == 0.0 { "Hiba".to_string() } else { (a / b).to_string() },
        _ => "Hiba".to_string(),
    }
}