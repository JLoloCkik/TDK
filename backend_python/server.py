import threading
from flask import Flask, request, jsonify
from flask_cors import CORS

from calculator import calculate
from ai import run_ai_task

app = Flask(__name__)
CORS(app)

@app.post('/api/calculate')
def calc():
    data = request.get_json()
    return jsonify(result=calculate(
        float(data['a']),
        float(data['b']),
        data['operator']
    ))

@app.post('/api/ai')
def ai_endpoint():
    data = request.get_json()
    # Külön szálon indítjuk az AI-t, hogy azonnal visszajelezzünk a frontendnek
    threading.Thread(target=run_ai_task, args=(data.get('text'),)).start()
    return jsonify(success=True), 200

if __name__ == '__main__':
    print("🐍 Python Backend fut a 5000-es porton!")
    app.run(port=5000, debug=True)