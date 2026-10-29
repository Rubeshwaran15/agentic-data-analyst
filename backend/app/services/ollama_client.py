import httpx
from app.core.config import settings


async def query_ollama_chat(system_prompt: str, user_prompt: str) -> str:
    """
    Sends a structured prompt to local Ollama HTTP API (Qwen2.5 1.5B)
    at http://127.0.0.1:11434 with timeout and error handling.
    """
    url = f"{settings.OLLAMA_BASE_URL}/api/chat"
    payload = {
        "model": settings.OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "options": {
            "temperature": 0.1,  # Low temperature for precise JSON formatting
            "num_predict": 1024,
        },
        "stream": False,
        "format": "json",  # Force Ollama to output valid JSON
    }

    async with httpx.AsyncClient(timeout=settings.OLLAMA_TIMEOUT_SECONDS) as client:
        try:
            response = await client.post(url, json=payload)
            if response.status_code != 200:
                raise RuntimeError(f"Ollama HTTP error status {response.status_code}: {response.text}")
            
            data = response.json()
            message_content = data.get("message", {}).get("content", "")
            return message_content
        except httpx.RequestError as exc:
            raise RuntimeError(f"Could not connect to Ollama at {settings.OLLAMA_BASE_URL}. Ensure Ollama is running locally.") from exc