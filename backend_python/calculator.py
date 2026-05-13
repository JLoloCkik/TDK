def calculate(a, b, op):
    if op == '+':
        return a + b
    if op == '-':
        return a - b
    if op == '*':
        return a * b
    if op == '/':
        return "Hiba: 0-val osztás" if b == 0 else a / b
    return "Ismeretlen művelet"