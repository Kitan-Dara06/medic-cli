import json
import os

from dotenv import load_dotenv

load_dotenv()
import requests


def query_model(prompt):
    api_key = os.getenv("API_KEY")
    if not api_key:
        return "Error: open_api_key not found"
    url = "https://api.openai.com/v1/chat/completions"

    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    payload = {
        "model": "gpt-4.1-mini",
        "messages": [{"role": "user", "content": prompt}],
    }
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        if response.status_code != 200:
            return f"Error {response.status_code}: {response.text}"
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Connection Error: {e}"
