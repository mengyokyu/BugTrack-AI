import json
import requests
from flask import current_app

def analyze_bug(title, description):
    key = current_app.config.get("AI_API_KEY")
    if not key:
        raise RuntimeError("AI analysis is not configured")
    prompt = ("Analyze this software bug and return JSON with keys summary, possible_cause, "
              "suggested_fix, suggested_severity. Severity must be LOW, MEDIUM, HIGH, or CRITICAL.\n"
              f"Title: {title}\nDescription: {description}")
    response = requests.post(current_app.config["AI_API_URL"], headers={"Authorization": f"Bearer {key}"},
        json={"model": current_app.config["AI_MODEL"], "messages":[{"role":"user","content":prompt}], "temperature":0.2}, timeout=20)
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"].replace("```json", "").replace("```", "").strip()
    data = json.loads(content)
    required = ["summary", "possible_cause", "suggested_fix", "suggested_severity"]
    if any(not data.get(k) for k in required): raise RuntimeError("AI returned an incomplete analysis")
    return data
