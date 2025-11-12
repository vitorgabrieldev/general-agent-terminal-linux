#!/usr/bin/env python3
import os
import sys
import json
import time
import requests
from dotenv import load_dotenv


# === Paths & Config ===
CONFIG_DIR   = os.path.expanduser("~/.config/ia")
ENV_PATH     = os.path.join(CONFIG_DIR, ".env")
HISTORY_PATH = os.path.join(CONFIG_DIR, "context.json")
MEMORY_PATH  = os.path.join(CONFIG_DIR, "memory.json")

os.makedirs(CONFIG_DIR, exist_ok=True)


# === Load Environment ===
load_dotenv(ENV_PATH)

API_KEY  = os.getenv("MISTRAL_API_KEY")
MODEL    = os.getenv("MISTRAL_MODEL", "mistral-small-2506")
API_URL  = os.getenv("MISTRAL_API_URL", "https://api.mistral.ai/v1/chat/completions")

if not API_KEY:
    print("❌ Error: Define your Mistral key in ~/.config/ia/.env (MISTRAL_API_KEY)")
    sys.exit(1)


# === Utility: Edit Memory ===
if "--memory" in sys.argv:
    os.system(f"{os.getenv('EDITOR', 'nano')} {MEMORY_PATH}")
    sys.exit(0)


# === Input Validation ===
if len(sys.argv) < 2:
    print("Usage: ia <question or task> | --memory")
    sys.exit(0)

prompt = " ".join(sys.argv[1:])


# === Ensure Config Files ===
if not os.path.exists(HISTORY_PATH):
    with open(HISTORY_PATH, "w") as f:
        json.dump([], f)

if not os.path.exists(MEMORY_PATH):
    default_memory = {
        "projects_dir": "/home/vitorgabrieldev/Projetos",
        "default_editor": "code",
        "preferred_lang": "English",
        "dev_notes": {
            "frontend": "use npm start",
            "backend": "run uvicorn app:app --reload"
        },
        "custom_paths": {
            "scripts": "/home/vitorgabrieldev/scripts",
            "dockerfiles": "/home/vitorgabrieldev/docker"
        }
    }
    with open(MEMORY_PATH, "w") as f:
        json.dump(default_memory, f, indent=2)


# === Load Contexts ===
with open(HISTORY_PATH, "r") as f:
    history = json.load(f)

try:
    with open(MEMORY_PATH, "r") as f:
        memory_context = json.load(f)
except Exception:
    memory_context = {}


# === Build Prompts ===
system_prompt = (
    "You are a Linux terminal assistant. "
    "Always respond ONLY in English. "
    "When the user asks something, generate between 2 and 5 possible Linux commands "
    "that solve the request. List them numbered, one per line, without explanations. "
    "Example: 'create a folder for my web project' → "
    "1. mkdir web-project\n2. mkdir -p ~/Documents/web-project\n3. mkdir -p ~/projects/web."
)

memory_text = "\n".join([f"{k}: {v}" for k, v in memory_context.items()])

merged_prompt = (
    f"{system_prompt}\n\n"
    f"System context memory:\n{memory_text}\n\n"
    "Use this context if it helps answer the user's request. "
    "If it's irrelevant, ignore it."
)

contextual_prompt = (
    f"{prompt}\n\n"
    f"(System context info: {memory_text})"
)

messages = (
    [{"role": "system", "content": merged_prompt}]
    + history
    + [{"role": "user", "content": contextual_prompt}]
)


# === Prepare API Request ===
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}",
}

data = {
    "model": MODEL,
    "messages": messages
}


# === API Request & Retry ===
print(f"🔹 Sending request to Mistral API ({MODEL})")
print(f"🔸 Prompt: {prompt}")

start_time = time.time()
for attempt in range(5):
    try:
        response = requests.post(API_URL, headers=headers, json=data)
        elapsed = round(time.time() - start_time, 2)
        print(f"🔹 Attempt {attempt + 1}: HTTP {response.status_code} (took {elapsed}s)")

        if response.status_code == 429:
            print("⚠️ Too many requests — waiting 5 seconds before retry...")
            time.sleep(5)
            continue

        response.raise_for_status()
        break

    except requests.exceptions.RequestException as e:
        print(f"❌ Network error on attempt {attempt + 1}: {e}")
        time.sleep(3)

else:
    print("❌ Failed after multiple attempts.")
    sys.exit(1)


# === Parse & Show Suggestions ===
try:
    result = response.json()
    content = result["choices"][0]["message"]["content"].strip()

    print("\n💡 AI Suggestions:\n")
    print(content)

except Exception as e:
    print(f"❌ Failed to parse response: {e}")
    print("Response text:")
    print(response.text)
    sys.exit(1)


# === User Selection ===
choice = input("\n👉 Select one option (1, 2, 3...) or press Enter to skip: ")

selected_cmd = None
if choice.strip().isdigit():
    lines = [l.strip() for l in content.splitlines() if l.strip()]
    idx = int(choice.strip()) - 1
    if 0 <= idx < len(lines):
        selected_cmd = lines[idx].split(". ", 1)[-1]


# === Execute Command ===
if selected_cmd:
    print(f"\n✅ Selected command:\n{selected_cmd}")
    confirm = input("Execute this command? [y/N] ").lower()
    if confirm == "y":
        print("🚀 Executing...")
        os.system(selected_cmd)
    else:
        print("❎ Execution cancelled.")
else:
    print("⚪ No valid option selected.")


# === Save Context ===
history.append({"role": "user", "content": prompt})
history.append({"role": "assistant", "content": content})

with open(HISTORY_PATH, "w") as f:
    json.dump(history[-10:], f, indent=2)

print("\n🧩 Context updated. Last 10 interactions saved.\n")
