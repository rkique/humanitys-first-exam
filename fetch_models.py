#!/usr/bin/env python3
"""Weekly snapshot job: query the latest model from each popular AI lab
across a fixed set of category prompts and cache the results as JSON for
the React frontend built in web/dist/. Run weekly by the GitHub Actions
workflow at .github/workflows/weekly.yml, which supplies the API key via
the OPENROUTER_API_KEY secret rather than the local openrouter.key file.
"""
import json
import os
import ssl
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

import certifi

SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
KEY_PATH = os.path.join(SCRIPT_DIR, "openrouter.key")
PROMPTS_PATH = os.path.join(SCRIPT_DIR, "prompts.json")
OUTPUT_PATH = os.path.join(SCRIPT_DIR, "web", "dist", "cache", "models_latest.json")
API_BASE = "https://openrouter.ai"

# One slot per popular lab: whichever model that lab most recently released
# on OpenRouter (by "created" timestamp) fills the slot. Order sets the
# color assignment, the on-page order, and the 3x3 minimap layout.
LAB_WATCHLIST = [
    "openai",
    "anthropic",
    "google",
    "meta-llama",
    "mistralai",
    "deepseek",
    "x-ai",
    "qwen",
    "moonshotai",
]

# Very short label for the top-right minimap tile, keyed by lab prefix.
LAB_ABBREV = {
    "openai": "GPT",
    "anthropic": "Claude",
    "google": "Gemini",
    "meta-llama": "Llama",
    "mistralai": "Mistral",
    "deepseek": "DeepSeek",
    "x-ai": "Grok",
    "qwen": "Qwen",
    "moonshotai": "Kimi",
}

# Windows 8 "Metro" tile palette, brightened for contrast against black text
# (Indigo and Violet brightened further since they read as too dark).
METRO_COLORS = [
    "#36ACE5",  # Cyan
    "#AFCB1F",  # Lime
    "#F2AE27",  # Amber
    "#E8301F",  # Red
    "#BF40FF",  # Violet
    "#1FB5B3",  # Teal
    "#F583D6",  # Pink
    "#974DFF",  # Indigo
    "#E6CF1F",  # Yellow
]

# Single source of truth for prompt copy, shared with the frontend: this
# file is the only place BASE_PROMPT/CATEGORIES text is written. The
# frontend never hardcodes prompt text either — it reads category.prompt
# out of the generated cache JSON, which is populated straight from here.
with open(PROMPTS_PATH) as _f:
    _prompts = json.load(_f)

BASE_PROMPT: str = _prompts["base_prompt"]
CATEGORIES: dict[str, str] = _prompts["categories"]


def load_key() -> str:
    if "OPENROUTER_API_KEY" in os.environ:
        return os.environ["OPENROUTER_API_KEY"]
    with open(KEY_PATH) as f:
        return f.read().strip()


def api_get(path: str, key: str) -> dict:
    req = urllib.request.Request(API_BASE + path, headers={"Authorization": f"Bearer {key}"})
    with urllib.request.urlopen(req, timeout=30, context=SSL_CONTEXT) as resp:
        return json.loads(resp.read())


def api_post(path: str, key: str, payload: dict) -> dict:
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        API_BASE + path,
        data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60, context=SSL_CONTEXT) as resp:
        return json.loads(resp.read())


# Utility/non-chat models (moderation classifiers, embedders, etc.) that
# happen to be a lab's most recently listed entry but would produce
# nonsense or one-word answers to a conversational prompt.
NON_CHAT_KEYWORDS = ["guard", "moderation", "embed", "rerank", "whisper", "tts", "stt"]


def is_chat_model(m: dict) -> bool:
    name = m["id"].lower()
    if any(kw in name for kw in NON_CHAT_KEYWORDS):
        return False
    return m.get("architecture", {}).get("output_modalities") == ["text"]


def get_latest_per_lab(key: str, watchlist: list[str]):
    models_index = api_get("/api/v1/models", key)["data"]

    resolved = []
    for i, prefix in enumerate(watchlist):
        candidates = [m for m in models_index if m["id"].startswith(prefix + "/")]
        chat_candidates = [m for m in candidates if is_chat_model(m)]
        if not chat_candidates:
            print(f"WARNING: no text-chat models found for lab '{prefix}', falling back to any model", file=sys.stderr)
            chat_candidates = candidates
        if not chat_candidates:
            print(f"WARNING: no models found for lab '{prefix}', skipping", file=sys.stderr)
            continue
        latest = max(chat_candidates, key=lambda m: m.get("created") or 0)
        resolved.append({
            "id": latest["id"],
            "name": latest["name"],
            "abbrev": LAB_ABBREV.get(prefix, prefix),
            "lab": prefix,
            "created": latest.get("created"),
            "color": METRO_COLORS[i % len(METRO_COLORS)],
        })
    return resolved


def query_one(key: str, model_id: str, prompt: str) -> dict:
    try:
        resp = api_post("/api/v1/chat/completions", key, {
            "model": model_id,
            "messages": [
                {"role": "system", "content": BASE_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 500,
            "usage": {"include": True},
        })
        if "error" in resp:
            return {"content": None, "error": resp["error"].get("message", "unknown error")}
        content = resp["choices"][0]["message"]["content"]
        usage = resp.get("usage", {})
        return {
            "content": content,
            "error": None,
            "cost": usage.get("cost"),
            "tokens": usage.get("total_tokens"),
        }
    except urllib.error.HTTPError as e:
        return {"content": None, "error": f"HTTP {e.code}: {e.read().decode(errors='replace')[:200]}"}
    except Exception as e:
        return {"content": None, "error": str(e)}


def main():
    key = load_key()
    models = get_latest_per_lab(key, LAB_WATCHLIST)
    if not models:
        print("No models resolved, aborting", file=sys.stderr)
        sys.exit(1)

    categories_out = {slug: {"prompt": prompt, "responses": {}} for slug, prompt in CATEGORIES.items()}
    jobs = [(slug, prompt, m["id"]) for slug, prompt in CATEGORIES.items() for m in models]

    total_cost = 0.0
    with ThreadPoolExecutor(max_workers=12) as pool:
        futures = {
            pool.submit(query_one, key, model_id, prompt): (slug, model_id)
            for slug, prompt, model_id in jobs
        }
        for fut in as_completed(futures):
            slug, model_id = futures[fut]
            result = fut.result()
            categories_out[slug]["responses"][model_id] = result
            if result.get("cost"):
                total_cost += result["cost"]

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "strategy": "latest model per popular lab",
        "total_cost": round(total_cost, 6),
        "models": models,
        "categories": categories_out,
    }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)
    print(f"Wrote {OUTPUT_PATH} (total cost: ${total_cost:.6f})")


if __name__ == "__main__":
    main()
