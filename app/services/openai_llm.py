from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_openai_completion(prompt: str, model: str = "gpt-3.5-turbo") -> str:
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content.strip()


def summarize_text(text: str, model: str = "gpt-3.5-turbo") -> str:
    """Return a short summary for the provided text using the OpenAI API."""
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "Summarize the following conversation in a concise manner.",
            },
            {"role": "user", "content": text},
        ],
    )
    return response.choices[0].message.content.strip()
