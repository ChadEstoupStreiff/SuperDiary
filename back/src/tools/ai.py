import json

import requests
import tiktoken
from views.settings import get_setting
from typing import Set

def request_llm(
    setting_prefix: str,
    prompt: str,
    input_text: str = None,
    stream_callback=None,
    max_tokens: int = None,
) -> Set[str]:
    """
    Request a language model (LLM) to process the prompt and return the response.
    Returns a tuple of (AI type, model, response).
    """
    ai_type = get_setting(f"{setting_prefix}_type")
    model = get_setting(f"{setting_prefix}_model")

    if input_text is not None:
        input_tokenized = tiktoken.encoding_for_model("gpt-3.5-turbo").encode(
            input_text
        )
        if max_tokens and len(input_tokenized) > max_tokens:
            input_text = tiktoken.encoding_for_model("gpt-3.5-turbo").decode(
                input_tokenized[:max_tokens]
            )

    if input_text is not None:
        prompt = prompt.replace("{input}", input_text)

    # LLAMA
    if ai_type == "llama":
        with requests.post(
            "http://ollama:11434/api/generate",
            json={"model": model, "prompt": prompt, "stream": True},
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
            "stream": stream_callback is not None,
        }
        url = "https://api.openai.com/v1/chat/completions"

        with requests.post(
            url, headers=headers, json=payload, stream=stream_callback is not None
        ) as response:
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
