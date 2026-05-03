import webbrowser
from threading import Timer
from flask import Flask, request, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)


@app.route('/api/calculate', methods=['POST'])
def calculate():
    data = request.json
    a, b, op = float(data['a']), float(data['b']), data['operator']
    res = 0
    if op == '+': res = a + b
    elif op == '-': res = a - b
    elif op == '*': res = a * b
    elif op == '/': res = "Hiba" if b == 0 else a / b
    return jsonify({"result": res})

@app.route('/api/ai', methods=['POST'])
    
def open_browser():
    path = os.path.abspath("index.html")
    webbrowser.open(f"file://{path}")

if __name__ == '__main__':
    Timer(1.5, open_browser).start()
    app.run(port=5000)