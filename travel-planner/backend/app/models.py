"""One provider setting shared by the travel agents and request router."""
import os

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from .gateway import create_gateway_model


def provider():
    return os.getenv('CHAT_PROVIDER', 'openai').strip().lower()


def is_configured():
    if provider() == 'helicone':
        return bool(os.getenv('HELICONE_API_KEY'))
    if provider() == 'gemini':
        return bool(os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY'))
    return provider() == 'openai' and bool(os.getenv('OPENAI_API_KEY'))


def create_model(agent_name='request-router'):
    if provider() == 'helicone':
        return create_gateway_model(agent_name)
    if provider() == 'gemini':
        key = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
        if not key:
            raise ValueError('Configure a Gemini API key in the project .env.')
        return ChatGoogleGenerativeAI(
            model=os.getenv('GEMINI_MODEL', 'gemini-3.1-flash-lite'),
            api_key=key, vertexai=False, temperature=0, max_tokens=6000,
            timeout=30, max_retries=0,
        )
    if provider() == 'openai':
        return ChatOpenAI(model=os.getenv('OPENAI_MODEL', 'gpt-4o-mini'),
                          temperature=0, timeout=30, max_retries=0)
    raise ValueError('CHAT_PROVIDER must be openai, gemini or helicone.')
