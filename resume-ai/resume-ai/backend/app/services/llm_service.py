import requests
from app.config import settings

class LLMService:
    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = "openrouter/free"

    def generate_response(self, prompt: str) -> str:
        try:
            if not self.api_key:
                raise Exception("OPENROUTER_API_KEY is missing. Set it in backend/.env and restart the backend.")

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": "openrouter/free",
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a professional resume writer. "
                            "Always return clean plain text resume content only. "
                            "Do not use markdown, asterisks, code fences, or quoted wrappers."
                        ),
                    },
                    {"role": "user", "content": prompt}
                ]
            }

            response = requests.post(self.url, headers=headers, json=payload, timeout=45)

            if response.status_code != 200:
                raise Exception(f"LLM Error: {response.text}")

            data = response.json()
            return data["choices"][0]["message"]["content"]

        except Exception as e:
            return f"Error: {str(e)}"


llm_service = LLMService()