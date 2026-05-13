import re
import sys
from pathlib import Path
import ollama

SCRIPT_PATH = Path(__file__).parent.absolute()
# Visszalép egyet, hogy megtalálja a TDK főmappát
PROJECT_ROOT = SCRIPT_PATH.parent if "backend" in SCRIPT_PATH.name else SCRIPT_PATH
MODEL_NAME = 'qwen2.5-coder:7b' # vagy 1.5b

IGNORED_DIRS = {'venv', '.venv', '__pycache__', '.git', 'node_modules'}

def load_context():
    context =[]
    valid_extensions = {'.js', '.html', '.css', '.py', '.rs'}
    for file_path in PROJECT_ROOT.rglob('*'):
        if any(ignored in file_path.parts for ignored in IGNORED_DIRS): continue
        if file_path.name == Path(__file__).name: continue
        if file_path.is_file() and file_path.suffix in valid_extensions:
            try:
                content = file_path.read_text(encoding='utf-8')
                rel_path = file_path.relative_to(PROJECT_ROOT)
                context.append(f"--- FILE: {rel_path} ---\n{content}")
            except: pass
    return "\n".join(context)

def apply_patches(ai_response):
    pattern = r'<patch path=["\'](.*?)["\']>\s*<search>(.*?)</search>\s*<replace>(.*?)</replace>\s*</patch>'
    matches = re.findall(pattern, ai_response, re.DOTALL | re.IGNORECASE)

    if not matches:
        print("Az AI nem küldött érvényes javítócsomagot.")
        return

    for path_str, search_text, replace_text in matches:
        target_path = PROJECT_ROOT / path_str.strip().replace("\\", "/")
        if not target_path.exists():
            print(f"Fájl nem található: {path_str}")
            continue

        original_content = target_path.read_text(encoding='utf-8')
        s_text, r_text = search_text.strip(), replace_text.strip()

        if s_text in original_content:
            new_content = original_content.replace(s_text, r_text)
            target_path.write_text(new_content, encoding='utf-8')
            print(f"SIKER: {path_str}")
        else:
            print(f"Nem találom a módosítandó részt: {path_str}")

def run_ai_task(user_request):
    codebase = load_context()
    system_msg = (
        "You are a headless code editor. Output ONLY XML patches. "
        "NO chat, NO explanations, NO markdown backticks. "
        "Format: <patch path=\"file\"><search>old</search><replace>new</replace></patch>"
    )
    prompt = f"TASK: {user_request}\n\nCODEBASE:\n{codebase}"
    print(f"AI dolgozik...")

    try:
        response = ollama.chat(
            model=MODEL_NAME,
            messages=[{'role': 'system', 'content': system_msg}, {'role': 'user', 'content': prompt}],
            options={'temperature': 0}
        )
        apply_patches(response['message']['content'])
    except Exception as e:
        print(f"[!!] Végzetes hiba: {e}")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        run_ai_task(sys.argv[1])