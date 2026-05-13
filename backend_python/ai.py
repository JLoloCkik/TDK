import ast
import re
import sys
from pathlib import Path

import ollama

# ---- CONFIG ----

SCRIPT_PATH = Path(__file__).resolve().parent

PROJECT_ROOT = (
    SCRIPT_PATH.parent
    if SCRIPT_PATH.name == "backend_python"
    else SCRIPT_PATH
)

MODEL_NAME = "qwen2.5-coder:7b"

IGNORED_DIRS = {
    "venv",
    ".venv",
    "__pycache__",
    ".git",
    "node_modules",
    "target"
}

VALID_EXTENSIONS = {
    ".py",
    ".js",
    ".html",
    ".css",
    ".rs"
}


# ---- CONTEXT LOADER ----

def load_context():
    context = []

    for file_path in PROJECT_ROOT.rglob("*"):

        # ignored dirs
        if any(
                ignored in file_path.parts
                for ignored in IGNORED_DIRS
        ):
            continue

        # self ignore
        if file_path.name == Path(__file__).name:
            continue

        # only files
        if not file_path.is_file():
            continue

        # only source files
        if file_path.suffix not in VALID_EXTENSIONS:
            continue

        try:

            content = file_path.read_text(
                encoding="utf-8"
            )

            rel_path = file_path.relative_to(
                PROJECT_ROOT
            )

            context.append(
                f"--- FILE: {rel_path} ---\n{content}"
            )

        except Exception:
            pass

    return "\n".join(context)


# ---- PATCH APPLY ----

def apply_patches(ai_response):
    print(f"DEBUG: AI válasz hossza: {len(ai_response)}")
    print(f"DEBUG: AI válasz:\n{ai_response[:200]}...")  # első 200 karakter

    # markdown cleanup
    ai_response = (
        ai_response
        .replace("```xml", "")
        .replace("```", "")
        .strip()
    )

    pattern = (
        r'<patch[^>]*path=["\']([^"\']*)["\'][^>]*>'
        r'\s*<search>(.*?)</search>'
        r'\s*<replace>(.*?)</replace>'
        r'\s*</patch>'
    )

    matches = re.findall(
        pattern,
        ai_response,
        re.DOTALL | re.IGNORECASE
    )

    if not matches:
        print("Az AI nem küldött patch-et.")
        return

    for path_str, s_text, r_text in matches:

        target_path = (
                PROJECT_ROOT /
                path_str.strip().replace("\\", "/")
        )

        if not target_path.exists():
            print(f"Fájl nem található: {path_str}")
            continue

        try:

            content = target_path.read_text(
                encoding="utf-8"
            )

        except Exception as e:
            print(f"Olvasási hiba: {e}")
            continue

        # FONTOS:
        # ne stripeljük a python indent miatt

        s_text = s_text.replace("\r\n", "\n")
        r_text = r_text.replace("\r\n", "\n")

        if s_text not in content:
            print(f"Nem találom a részt: {path_str}")
            continue

        # csak első találat
        new_content = content.replace(
            s_text,
            r_text,
            1
        )

        # python syntax védelem
        if target_path.suffix == ".py":

            try:
                ast.parse(new_content)

            except SyntaxError as e:
                print(
                    f"Python syntax hiba "
                    f"{path_str}: {e}"
                )
                continue

        try:

            target_path.write_text(
                new_content,
                encoding="utf-8"
            )

            print(f"SIKER: {path_str}")

        except Exception as e:
            print(f"Írási hiba: {e}")


# ---- AI TASK ----

def run_ai_task(user_request):
    codebase = load_context()

    system_msg = (
        "You are a headless code editor. "
        "Output XML patches in this exact format, nothing else:\n"
        "<patch path=\"backend_python/ai.py\">"
        "<search>old code</search>"
        "<replace>new code</replace>"
        "</patch>\n\n"
        "NO markdown. NO explanations. NO other text."
    )

    prompt = (
        f"TASK:\n{user_request}\n\n"
        f"CODEBASE:\n{codebase}"
    )

    print("AI dolgozik...")

    try:

        response = ollama.chat(
            model=MODEL_NAME,

            messages=[
                {
                    "role": "system",
                    "content": system_msg
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],

            options={
                "temperature": 0
            }
        )

        ai_text = response["message"]["content"]

        apply_patches(ai_text)

    except Exception as e:
        print(f"Végzetes hiba: {e}")


# ---- ENTRY ----

if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Adj meg taskot.")
        sys.exit(1)

    run_ai_task(sys.argv[1])
