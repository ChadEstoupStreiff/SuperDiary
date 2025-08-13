import json
import re
from typing import Set

import requests
from bs4 import BeautifulSoup
from views.settings import get_setting


def parse_token_count(size_str: str) -> int:
    size_str = size_str.strip().upper()
    if size_str.endswith("K"):
        return int(float(size_str[:-1]) * 1024)
    elif size_str.endswith("M"):
        return int(float(size_str[:-1]) * 1024 * 1024)
    else:
        return int(size_str)


def get_context_size(model_name: str, default: int = 4096) -> str:
    base_url = "https://ollama.com/library/"
    model_slug = model_name.split(":")[0]
    url = f"{base_url}{model_slug}"

    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch page: {url}")

    soup = BeautifulSoup(response.text, "html.parser")

    # Search all mobile cards (sm:hidden blocks) for matching model name
    model_cards = soup.find_all("a", class_="sm:hidden")
    for card in model_cards:
        name_tag = card.find("p", class_="block")
        if name_tag and model_name in name_tag.text:
            info_text = card.get_text()
            match = re.search(r"(\d+K)\s+context window", info_text)
            if match:
                return match.group(1)

    return default


def request_llm(
    setting_prefix: str,
    prompt: str,
    input_text: str = None,
    stream_callback=None,
) -> Set[str]:
    """
    Request a language model (LLM) to process the prompt and return the response.
    Returns a tuple of (AI type, model, response).
    """
    ai_type = get_setting(f"{setting_prefix}_type")
    model = get_setting(f"{setting_prefix}_model")

    if input_text is not None:
        prompt = prompt.replace("{input}", input_text)

    # LLAMA
    if ai_type == "llama":
        ollama_server = get_setting("ollama_server", "http://ollama:11434")
        with requests.post(
            f"{ollama_server}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": True,
                "options": {
                    "num_ctx": parse_token_count(get_context_size(model)),
                    "num_keep": 2048,
                },
            },
            stream=True,
            timeout=3600,
        ) as response:
            if response.status_code != 200:
                raise Exception(f"LLM error {response.status_code}: {response.text}")

            output = ""
            for line in response.iter_lines():
                if line:
                    part = line.decode("utf-8")
                    if part.startswith("data: "):
                        part = part[6:]
                    try:
                        data = json.loads(part)
                        chunk = data.get("response", "")
                        output += chunk
                        if stream_callback:
                            stream_callback(chunk)
                    except Exception:
                        pass
            return ai_type, model, output

    # Mistral
    elif ai_type == "Mistral":
        api_key = get_setting("mistral_api_key")
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": True,
        }
        url = "https://api.mistral.ai/v1/chat/completions"
        with requests.post(url, headers=headers, json=payload, stream=True) as response:
            if response.status_code != 200:
                raise Exception(
                    f"Mistral error {response.status_code}: {response.text}"
                )

            output = ""
            for line in response.iter_lines():
                if line:
                    line = line.decode("utf-8")
                    if line.startswith("data: "):
                        line = line[6:]
                    if line == "[DONE]":
                        break
                    try:
                        data = json.loads(line)
                        chunk = data["choices"][0]["delta"].get("content", "")
                        output += chunk
                        if stream_callback:
                            stream_callback(chunk)
                    except Exception:
                        pass
            return ai_type, model, output

    # ChatGPT
    elif ai_type == "ChatGPT":
        api_key = get_setting("openai_api_key")
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": True,
        }
        url = "https://api.openai.com/v1/chat/completions"

        with requests.post(url, headers=headers, json=payload, stream=True) as response:
            if response.status_code != 200:
                raise Exception(f"OpenAI error {response.status_code}: {response.text}")

            output = ""
            for line in response.iter_lines():
                if line:
                    line = line.decode("utf-8").replace("data: ", "")
                    if line == "[DONE]":
                        break
                    try:
                        data = json.loads(line)
                        chunk = data["choices"][0]["delta"].get("content", "")
                        output += chunk
                        if stream_callback:
                            stream_callback(chunk)
                    except Exception:
                        pass
            return ai_type, model, output

    # Gemini
    elif ai_type == "Gemini":
        api_key = get_setting("gemini_api_key")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}

        response = requests.post(url, json=payload)
        if response.status_code != 200:
            raise Exception(f"Gemini error {response.status_code}: {response.text}")

        try:
            data = response.json()
            output = data["candidates"][0]["content"]["parts"][0]["text"]
            if stream_callback:
                stream_callback(output)
            return ai_type, model, output
        except Exception as e:
            raise Exception(f"Gemini response error: {e}")

    else:
        raise ValueError(f"Unsupported AI type: {ai_type}")
