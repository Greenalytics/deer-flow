import litellm

SGLANG_BASE_URL = "http://localhost:30000/v1"
MODEL = "openai/google/gemma-4-E4B-it"


def chat(message: str) -> str:
    response = litellm.completion(
        model=MODEL,
        messages=[{"role": "user", "content": message}],
        api_base=SGLANG_BASE_URL,
        api_key="not-required",
    )
    return response.choices[0].message.content


if __name__ == "__main__":
    reply = chat("Hello! Who are you and what can you do?")
    print(reply)
