from flask import Flask, request, jsonify
from flask_cors import CORS

from ai import run_ai_task

app = Flask(__name__)
CORS(app)


# ---- Calculator ----
def calculate(a, b, op):
    if op == '+': return a + b
    if op == '-': return a - b
    if op == '*': return a * b
    if op == '/': return "Hiba" if b == 0 else a / b
    return "Hiba"


# ---- API ----
@app.post('/api/calculate')
def calc():
    data = request.get_json()
    return jsonify(result=calculate(
        float(data['a']),
        float(data['b']),
        data['operator']
    ))

@app.post('/api/ai')
def ai():
    data = request.get_json()
    run_ai_task(data.get('text'))
    return jsonify(success=True), 200

if __name__ == '__main__':
    app.run(port=5000, debug=True)