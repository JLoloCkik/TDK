use regex::Regex;
use std::fs;
use std::path::{Path, PathBuf};
use walkdir::WalkDir;

const MODEL: &str = "qwen2.5-coder:7b";

const IGNORED_DIRS: &[&str] = &[
    ".git",
    "venv",
    ".venv",
    "node_modules",
    "__pycache__",
    "target",
];

fn project_root() -> PathBuf {
    let current = std::env::current_dir().unwrap();

    if current.file_name().unwrap() == "backend_rust" {
        current.parent().unwrap().to_path_buf()
    } else {
        current
    }
}

fn is_ignored(path: &Path) -> bool {
    path.components().any(|c| {
        let s = c.as_os_str().to_string_lossy();
        IGNORED_DIRS.contains(&s.as_ref())
    })
}

fn load_context() -> String {
    let root = project_root();

    let extensions = ["rs", "py", "js", "html", "css"];

    let mut result = String::new();

    for entry in WalkDir::new(&root)
        .into_iter()
        .filter_map(Result::ok)
    {
        let path = entry.path();

        if is_ignored(path) {
            continue;
        }

        if !path.is_file() {
            continue;
        }

        let ext = match path.extension().and_then(|e| e.to_str()) {
            Some(e) => e,
            None => continue,
        };

        if !extensions.contains(&ext) {
            continue;
        }

        if let Ok(content) = fs::read_to_string(path) {
            if let Ok(rel) = path.strip_prefix(&root) {
                result.push_str(
                    &format!(
                        "--- FILE: {} ---\n{}\n",
                        rel.display(),
                        content
                    )
                );
            }
        }
    }

    result
}

fn apply_patches(ai_response: &str) {
    let root = get_project_root();
    let re = Regex::new(r"(?is)<patch path=[\x22\x27](.*?)[\x22\x27]>\s*<search>(.*?)</search>\s*<replace>(.*?)</replace>").unwrap();

    let mut found = false;
    for cap in re.captures_iter(ai_response) {
        found = true;
        let path_str = cap[1].trim();
        let search = cap[2].trim();
        let replace = cap[3].trim();

        let target_path = root.join(path_str);
        if target_path.exists() {
            if let Ok(content) = fs::read_to_string(&target_path) {
                if content.contains(search) {
                    let new_content = content.replace(search, replace);
                    fs::write(&target_path, new_content).unwrap();
                    println!("SIKER: {}", path_str);
                } else {
                    println!("HIBA: Nem található a keresett rész: {}", path_str);
                }
            }
        } else {
            println!("HIBA: A fájl nem létezik: {}", path_str);
        }
    }

    if !found {
        println!("Az AI nem küldött érvényes javítócsomagot.");
    }
}

    let cleaned = ai_response
        .replace("```xml", "")
        .replace("```", "");

    let regex = Regex::new(
        r#"(?s)<patch path=["'](.*?)["']>\s*<search>(.*?)</search>\s*<replace>(.*?)</replace>\s*</patch>"#
    ).unwrap();

    let root = project_root();

    let mut found = false;

    for cap in regex.captures_iter(&cleaned) {

        found = true;

        let path_str = cap[1].trim().replace("\\", "/");

        let search = cap[2].trim();

        let replace = cap[3].trim();

        let target = root.join(path_str);

        if !target.exists() {
            println!("Fájl nem található");
            continue;
        }

        let content = match fs::read_to_string(&target) {
            Ok(v) => v,
            Err(_) => continue,
        };

        if !content.contains(search) {
            println!("Nincs találat");
            continue;
        }

        let updated = content.replacen(search, replace, 1);

        if fs::write(&target, updated).is_ok() {
            println!("PATCH OK");
        }
    }

    if !found {
        println!("Nincs patch");
    }
}

pub async fn run_ai_task(task: String) {

    println!("AI dolgozik...");

    let codebase = load_context();

    let system_prompt = concat!(
        "You are a headless code editor. ",
        "Output ONLY XML patches. ",
        "No markdown. ",
        "No explanations. ",
        "Format: ",
        "<patch path=\"file\">",
        "<search>old</search>",
        "<replace>new</replace>",
        "</patch>"
    );

    let payload = serde_json::json!({
        "model": MODEL,
        "stream": false,
        "options": {
            "temperature": 0
        },
        "messages": [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": format!(
                    "TASK: {}\n\nCODEBASE:\n{}",
                    task,
                    codebase
                )
            }
        ]
    });

    let client = reqwest::Client::new();

    match client
        .post("http://127.0.0.1:11434/api/chat")
        .json(&payload)
        .send()
        .await
    {
        Ok(res) => {

            match res.json::<serde_json::Value>().await {

                Ok(json) => {

                    if let Some(content) =
                        json["message"]["content"].as_str()
                    {
                        apply_patches(content);
                    }
                }

                Err(e) => {
                    println!("JSON HIBA: {}", e);
                }
            }
        }

        Err(e) => {
            println!("REQWEST HIBA: {}", e);
        }
    }
}