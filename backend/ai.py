import re
import sys
from pathlib import Path
import ollama

class Config:
    SCRIPT_PATH = Path(__file__).parent.absolute()
    PROJECT_ROOT = SCRIPT_PATH.parent if "backend" in SCRIPT_PATH.name else SCRIPT_PATH
    MODEL_NAME = 'qwen2.5-coder:7b'

    IGNORED_DIRS = {'.venv', 'venv', '__pycache__', '.git', 'node_modules'}
    VALID_EXTENSIONS = {'.js', '.html', '.css', '.py', '.rs'}


class FileManager:

    @staticmethod
    def normalize_text(text: str) -> str:
        return re.sub(r'\s+', ' ', text).strip()

    @classmethod
    def load_context(cls) -> str:
        context =[]
        for file_path in Config.PROJECT_ROOT.rglob('*'):
            if cls._should_ignore(file_path):
                continue

            if file_path.is_file() and file_path.suffix in Config.VALID_EXTENSIONS:
                try:
                    content = file_path.read_text(encoding='utf-8')
                    rel_path = file_path.relative_to(Config.PROJECT_ROOT)
                    context.append(f"--- FILE: {rel_path} ---\n{content}")
                except Exception:
                    pass
        return "\n".join(context)

    @classmethod
    def apply_patches(cls, ai_response: str) -> None:

        pattern = r'<patch path=["\'](.*?)["\']>\s*<search>(.*?)</search>\s*<replace>(.*?)</replace>\s*</patch>'
        matches = re.findall(pattern, ai_response, re.DOTALL | re.IGNORECASE)

        if not matches:
            print("[!] HIBA: Az AI nem küldött érvényes javítócsomagot (XML patch hiányzik).")
            return

        for path_str, search_text, replace_text in matches:
            cls._apply_single_patch(path_str, search_text, replace_text)

    @classmethod
    def _apply_single_patch(cls, path_str: str, search_text: str, replace_text: str) -> None:
        target_path = Config.PROJECT_ROOT / path_str.strip().replace("\\", "/")

        if not target_path.exists():
            print(f"[!] HIBA: Fájl nem található: {path_str}")
            return

        original_content = target_path.read_text(encoding='utf-8')
        s_text = search_text.strip()
        r_text = replace_text.strip()

        if cls.normalize_text(s_text) in cls.normalize_text(original_content):
            new_content = original_content.replace(s_text, r_text)
            target_path.write_text(new_content, encoding='utf-8')
            print(f"[+] SIKER: {path_str}")
        else:
            print(f"[!] HIBA: Nem találom a módosítandó részt itt: {path_str}")

    @staticmethod
    def _should_ignore(file_path: Path) -> bool:
        in_ignored_dir = any(ignored in file_path.parts for ignored in Config.IGNORED_DIRS)
        is_self = file_path.name == Path(__file__).name
        return in_ignored_dir or is_self


class AICodeEditor:

    def __init__(self):
        self.model = Config.MODEL_NAME

    def _get_system_message(self) -> str:
        return (
            "You are a Senior Developer. Your only goal is to write correct, error-free code patches.\n"
            "Output ONLY XML patches. NO chat, NO explanations, NO markdown.\n\n"
            "CRITICAL RULE FOR PYTHON (.py files):\n"
            "Python is extremely sensitive to indentation. A single wrong space will cause an IndentationError and crash the server. "
            "Use 'elif' for subsequent conditions, do not nest 'if' statements incorrectly.\n\n"
            "EXAMPLE of adding a new operator to `calculator.py`:\n"
            "<patch path=\"backend_python/calculator.py\">\n"
            "<search>\n"
            "    if op == '/': return \"Hiba: 0-val osztás\" if b == 0 else a / b\n"
            "    return \"Ismeretlen művelet\"\n"
            "</search>\n"
            "<replace>\n"
            "    if op == '/': return \"Hiba: 0-val osztás\" if b == 0 else a / b\n"
            "    elif op == '%': return a % b\n"
            "    return \"Ismeretlen művelet\"\n"
            "</replace>\n"
            "</patch>\n\n"
            "Format: <patch path=\"file\"><search>old code</search><replace>new code</replace></patch>"
        )

    def process_task(self, user_request: str) -> None:
        codebase = FileManager.load_context()
        prompt = f"TASK: {user_request}\n\nCODEBASE:\n{codebase}"

        print(f"[*] AI dolgozik ({self.model})...")

        try:
            response = ollama.chat(
                model=self.model,
                messages=[
                    {'role': 'system', 'content': self._get_system_message()},
                    {'role': 'user', 'content': prompt}
                ],
                options={'temperature': 0}
            )
            FileManager.apply_patches(response['message']['content'])

        except Exception as e:
            print(f"[!!] Végzetes AI hiba: {e}")


def run_ai_task(user_request: str) -> None:
    editor = AICodeEditor()
    editor.process_task(user_request)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        run_ai_task(sys.argv[1])
    else:
        print("Kérlek, adj meg egy feladatot argumentumként!")