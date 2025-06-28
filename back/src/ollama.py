import requests
import tiktoken


def request_ollama(
    model: str,
    prompt: str,
    input_text: str = None,
    max_tokens: int = 2048,  # 4086 / 2
):
    if input_text is not None:
        input_tokenized = tiktoken.encoding_for_model("gpt-3.5-turbo").encode(
            input_text
        )
        if len(input_tokenized) > max_tokens:
            truncated_input = tiktoken.encoding_for_model("gpt-3.5-turbo").decode(
                input_tokenized[:max_tokens]
            )
        else:
            truncated_input = input_text

        formatted_prompt = prompt.replace("{input}", truncated_input)
    else:
        formatted_prompt = prompt
    
    response = requests.post(
        "http://ollama:11434/api/generate",
        json={"model": model, "prompt": formatted_prompt, "stream": False},
        timeout=3600,
    )

    if response.status_code == 200:
        return response.json()["response"]
    else:
        raise Exception(f"Ollama error {response.status_code}: {response.text}")
