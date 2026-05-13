import ast
import re
from pathlib import Path
import threading
import traceback
import ollama

MODEL_NAME = "qwen2.5-coder:7b"

IGNORED_DIRS = {"venv", ".venv", "__pycache__", ".git", "node_modules", "target"}
VALID_EXTENSIONS = {".py", ".js", ".html", ".css", ".rs"}


class ProjectScanner:
    def __init__(self, root: Path):
        self.root = root
        self.files = {}

    def scan(self) -> None:
        for path in self.root.rglob("*"):
            if self._should_skip(path):
                continue
            try:
                content = path.read_text(encoding="utf-8")
                rel = str(path.relative_to(self.root))
                self.files[rel] = content
            except Exception:
                pass

    def _should_skip(self, path: Path) -> bool:
        if not path.is_file() or path.suffix not in VALID_EXTENSIONS:
            return True
        if any(ig in path.parts for ig in IGNORED_DIRS):
            return True
        if path.name == "ai.py":
            return True
        return False

    def to_context(self) -> str:
        return "\n".join(f"=== FILE: {p} ===\n{c}\n" for p, c in sorted(self.files.items()))


class PatchManager:
    PATCH_RE = re.compile(
        r'<patch[^>]*path=["\']([^"\']+)["\'][^>]*>\s*<search>(.*?)</search>\s*<replace>(.*?)</replace>\s*</patch>',
        re.DOTALL | re.IGNORECASE,
        )

    def __init__(self, root: Path):
        self.root = root

    def apply_all(self, ai_response: str) -> dict:
        cleaned = ai_response.replace("```xml", "").replace("```", "").strip()
        matches = self.PATCH_RE.findall(cleaned)
        stats = {"success": 0, "failed": 0, "details": []}

        if not matches:
            stats["details"].append("No patches found in AI response.")
            return stats

        for fpath, search, replace in matches:
            ok, msg = self._apply_single(fpath, search, replace)
            if ok:
                stats["success"] += 1
            else:
                stats["failed"] += 1
            stats["details"].append({"file": fpath, "ok": ok, "msg": msg})

        return stats

    def _apply_single(self, fpath: str, search: str, replace: str):
        target = self.root / fpath.strip().replace("\\", "/")
        if not target.exists():
            return False, "File not found"

        try:
            content = target.read_text(encoding="utf-8")
        except Exception as e:
            return False, f"Read error: {e}"

        search_norm = search.replace("\r\n", "\n")
        replace_norm = replace.replace("\r\n", "\n")

        if search_norm not in content:
            return False, "Search text not found"

        new_content = content.replace(search_norm, replace_norm, 1)

        if target.suffix == ".py":
            try:
                ast.parse(new_content)
            except SyntaxError as e:
                return False, f"Python syntax error after patch: {e}"

        try:
            target.write_text(new_content, encoding="utf-8")
            return True, "Patched"
        except Exception as e:
            return False, f"Write error: {e}"


class CodeEditor:
    def __init__(self, project_root: Path):
        self.root = project_root
        self.scanner = ProjectScanner(self.root)
        self.patcher = PatchManager(self.root)

    def build_system_prompt(self) -> str:
        return (
            "You are a FULL-STACK CODE MODIFIER. Output ONLY XML patches, nothing else.\n"
            "RULES:\n"
            " - Return only XML <patch> elements, no explanation, no markdown.\n"
            " - Each <patch> should modify one exact location in one file.\n"
            " - Preserve exact indentation and whitespace in search/replace.\n"
            " - If you add UI elements, modify frontend/index.html, frontend/script.js and frontend/style.css accordingly.\n"
            " - Update backend_python/calculator.py and backend_rust/src/calculator.rs for new operations.\n"
            "FORMAT:\n"
            "<patch path=\"relative/path/to/file\">\n"
            "<search>EXACT old code</search>\n"
            "<replace>EXACT new code</replace>\n"
            "</patch>\n"
        )

    def build_user_prompt(self, task: str, context: str) -> str:
        return f"TASK: {task}\n\nCODEBASE:\n{context}\n\nGenerate all XML patches required to complete the task across the whole repo."

    def run_model(self, prompt_system: str, prompt_user: str) -> str:
        try:
            response = ollama.chat(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": prompt_system},
                    {"role": "user", "content": prompt_user},
                ],
                options={"temperature": 0},
            )
            return response["message"]["content"]
        except Exception:
            return f""  # return empty on failure

    def execute(self, task: str) -> dict:
        self.scanner.scan()
        context = self.scanner.to_context()
        system_prompt = self.build_system_prompt()
        user_prompt = self.build_user_prompt(task, context)
        ai_response = self.run_model(system_prompt, user_prompt)
        if not ai_response:
            return {"success": 0, "failed": 0, "error": "No response from model"}
        stats = self.patcher.apply_all(ai_response)
        return stats


def get_project_root() -> Path:
    script_dir = Path(__file__).resolve().parent
    return script_dir.parent if script_dir.name == "backend_python" else script_dir


def run_ai_task(user_request: str) -> dict:
    """
    Public function used by server.py to start a task.
    Runs synchronously; server can call it in a background thread.
    Returns stats dict.
    """
    try:
        editor = CodeEditor(get_project_root())
        result = editor.execute(user_request)
        return result
    except Exception:
        traceback.print_exc()
        return {"success": 0, "failed": 0, "error": "internal exception"}