from pathlib import Path
from flask import Flask, request, jsonify
import ollama
from calculator import app


def load_rules(mappa=".cursorrules"):
    p = Path(mappa)
    tartalom = ""
    for fajl_utvonal in p.iterdir():
        if fajl_utvonal.is_file():
            with open(fajl_utvonal, 'r', encoding='utf-8') as f:
                tartalom += f.read()

    return tartalom



system_rules = load_rules(".cursorrules")

messages = [
    {'role': 'system', 'content': system_rules},
    {'role': 'user', 'content': 'create calculator'}
]


stream = ollama.chat(
    model='qwen2.5-coder:7b',
    messages=messages,
    stream=True,
    options={'temperature': 0.1}
)

for chunk in stream:
    print(chunk['message']['content'], end='', flush=True)