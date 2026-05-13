use regex::Regex;
use std::fs;
use std::path::PathBuf;
use walkdir::WalkDir;

const MODEL: &str = "qwen2.5-coder:7b"; // Vagy 1.5b

fn get_project_root() -> PathBuf {
    let mut current = std::env::current_dir().unwrap();
    if current.file_name().unwrap() == "backend_rust" {
        current.pop(); // Visszalép a TDK mappába
    }
    current
}

fn get_codebase() -> String {
    let root = get_project_root();
    let mut docs = String::new();
    let exts = vec!["js", "html", "css", "py", "rs"];

    for entry in WalkDir::new(&root).into_iter().filter_map(|e| e.ok()) {
        let path = entry.path();
        let path_str = path.to_string_lossy();
        if path.is_file() && !path_str.contains(".git") && !path_str.contains("venv") && !path_str.contains("node_modules") {
            if let Some(ext) = path.extension().and_then(|e| e.to_str()) {
                if exts.contains(&ext) {
                    if let Ok(content) = fs::read_to_string(path) {
                        let rel_path = path.strip_prefix(&root).unwrap();
                        docs.push_str(&format!("--- FILE: {} ---\n{}\n", rel_path.display(), content));
                    }
                }
            }
        }
    }
    docs
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

pub async fn run_ai_task(prompt: String) {
    println!("AI dolgozik...");
    let codebase = get_codebase();
    let client = reqwest::Client::new();

    let system_msg = "You are a headless code editor. Output ONLY XML patches. NO chat, NO explanations, NO markdown backticks. Format: <patch path=\"file\"><search>old</search><replace>new</replace></patch>";

    let payload = serde_json::json!({
        "model": MODEL,
        "options": { "temperature": 0 },
        "stream": false,
        "messages":[
            { "role": "system", "content": system_msg },
            { "role": "user", "content": format!("TASK: {}\n\nCODEBASE:\n{}", prompt, codebase) }
        ]
    });

    if let Ok(res) = client.post("http://127.0.0.1:11434/api/chat").json(&payload).send().await {
        if let Ok(json_res) = res.json::<serde_json::Value>().await {
            if let Some(content) = json_res["message"]["content"].as_str() {
                apply_patches(content);
            }
        }
    }
}