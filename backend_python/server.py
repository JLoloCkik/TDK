import threading
from flask import Flask, request, jsonify
from flask_cors import CORS
from ai import run_ai_task, get_project_root

app = Flask(__name__)
CORS(app)


@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "ok", "root": str(get_project_root())})


@app.post("/api/calculate")
def calc():
    data = request.get_json() or {}
    try:
        a = float(data.get("a", 0))
        b = float(data.get("b", 0))
        operator = data.get("operator", "+")
    except Exception:
        return jsonify({"error": "invalid input"}), 400

    # simple local call to calculator module
    from calculator import calculate
    res = calculate(a, b, operator)
    return jsonify(result=res)


@app.post("/api/ai")
def ai_endpoint():
    data = request.get_json() or {}
    task = data.get("text") or data.get("task") or ""
    if not task:
        return jsonify({"error": "task text is required"}), 400

    def _background():
        try:
            stats = run_ai_task(task)
            print("AI task finished:", stats)
        except Exception as e:
            print("AI task error:", e)

    thread = threading.Thread(target=_background, daemon=True)
    thread.start()

    return jsonify({"success": True, "message": "AI task started"}), 200


if __name__ == "__main__":
    print("🐍 Python Backend running on port 5000")
    app.run(port=5000, debug=True)