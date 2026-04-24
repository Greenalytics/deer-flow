import litellm
import os

# Configuration for the local vLLM server
MODEL_NAME = "openai/gemma-4-E4B-it-GPTQ"  # vLLM is OpenAI-compatible
API_BASE = "http://localhost:8000/v1"

def chat_with_gemma(prompt):
    print(f"Sending prompt to {MODEL_NAME} at {API_BASE}...")
    try:
        response = litellm.completion(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            api_base=API_BASE,
            # No API key needed for local vLLM by default, 
            # but LiteLLM might require a placeholder if not set
            api_key="none" 
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    user_prompt = "What are the benefits of using quantization like GPTQ for LLMs?"
    answer = chat_with_gemma(user_prompt)
    print("\n--- Response ---")
    print(answer)
