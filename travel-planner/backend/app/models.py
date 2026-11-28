"""One Gemini connection: use Helicone when its key is present."""
import os

from langchain_google_genai import ChatGoogleGenerativeAI

helicone_key = os.getenv('HELICONE_API_KEY')
headers = {'Helicone-Auth': f'Bearer {helicone_key}', 'Helicone-Target-URL': 'https://generativelanguage.googleapis.com',
           'Helicone-Omit-Request': 'true', 'Helicone-Omit-Response': 'true'} if helicone_key else {}
model = ChatGoogleGenerativeAI(
    model=os.getenv('GEMINI_MODEL', 'gemini-3.1-flash-lite'), api_key=os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY'),
    base_url='https://gateway.helicone.ai' if helicone_key else None, additional_headers=headers,
    vertexai=False, temperature=0, max_tokens=6000, timeout=60, max_retries=0,
)
