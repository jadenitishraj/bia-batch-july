"""Helicone's hosted AI Gateway; only its dedicated key leaves this process."""
import os

from google.genai.types import GenerateContentResponse
from langchain_google_genai.chat_models import _response_to_result
from langchain_openai import ChatOpenAI


class GatewayChatOpenAI(ChatOpenAI):
    """Use the pinned Gemini parser when BYOK returns native Google responses."""

    def _create_chat_result(self, response, generation_info=None):
        data = response if isinstance(response, dict) else response.model_dump()
        if not data.get('choices') and data.get('candidates'):
            native = {key: data[key] for key in (
                'candidates', 'usageMetadata', 'modelVersion', 'responseId', 'promptFeedback'
            ) if key in data}
            return _response_to_result(GenerateContentResponse.model_validate(native, extra='ignore'))
        return super()._create_chat_result(response, generation_info)


def create_gateway_model(agent_name):
    key = os.getenv('HELICONE_API_KEY')
    if not key:
        raise ValueError('Configure HELICONE_API_KEY in the ignored project .env.')
    headers = {
        'Helicone-Property-App': 'bia-july-travel-planner',
        'Helicone-Property-Agent': agent_name,
        'Helicone-Omit-Request': 'true',
        'Helicone-Omit-Response': 'true',
    }
    return GatewayChatOpenAI(
        model=os.getenv('HELICONE_MODEL', 'gemini-3.1-flash-lite/google-ai-studio'),
        api_key=key, base_url='https://ai-gateway.helicone.ai/v1',
        default_headers=headers, temperature=0, max_tokens=6000,
        timeout=60, max_retries=0, use_responses_api=False,
    )
