import google.generativeai as genai
from groq import Groq
from backend.config import settings

genai.configure(api_key=settings.GEMINI_API_KEY)
groq_client = Groq(api_key=settings.GROQ_API_KEY)

def generate_text(
    prompt: str,
    temperature: float = 0.2,
    max_tokens: int = 1024,
    model_name: str | None = None,
):
    """Generate text using Gemini and fall back to Groq on any failure."""
    if model_name is None:
        model_name = settings.GEMINI_MODEL

    try:
        model = genai.GenerativeModel(
            model_name=model_name,
        )

        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            },
        )
        print("Using GEMINI")
        return {
            "provider": "gemini",
            "text": response.text.strip(),
        }

    except Exception as e:
        print("Gemini failed:", e)
        print("Switching to Groq...")

        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            temperature=temperature,
        )
        print("Using GROQ")
        return {
            "provider": "groq",
            "text": response.choices[0].message.content.strip(),
        }
    