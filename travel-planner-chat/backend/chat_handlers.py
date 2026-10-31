"""Authenticated chat endpoint. Existing trip endpoints still enforce ownership."""
from botocore.exceptions import BotoCoreError, ClientError
from chat_graph import answer_chat
from langchain_core.tools import ToolException
from langgraph.errors import GraphRecursionError
from trip_tools import make_trip_tools, trip_request


def validate_chat(payload):
    if not isinstance(payload, dict) or set(payload) - {'message', 'history'}:
        raise ValueError('Send a message and optional history.')
    message = payload.get('message')
    history = payload.get('history', [])
    if not isinstance(message, str) or not 1 <= len(message.strip()) <= 2000:
        raise ValueError('Write a message between 1 and 2000 characters.')
    if not isinstance(history, list) or len(history) > 12:
        raise ValueError('History must contain at most 12 messages.')
    for item in history:
        if (not isinstance(item, dict) or set(item) != {'role', 'content'}
                or item['role'] not in ('user', 'assistant')
                or not isinstance(item['content'], str) or not 1 <= len(item['content']) <= 8000):
            raise ValueError('History must contain user and assistant text only.')
    return message.strip(), history


class ChatHandlers:
    def chat_route(self, path):
        if path != '/api/chat':
            return False
        if self.command != 'POST':
            self.respond(405, {'error': 'Method not allowed.'})
        elif self.authorize():
            message, history = validate_chat(self.read_json())
            if self.server.chat_limit.allow('chat'):
                self.reply_to_chat(message, history)
            else:
                self.respond(429, {'error': 'The class demo allows 10 chat requests per minute. Please wait.'})
        return True

    def reply_to_chat(self, message, history):
        # Use our listening address, not a caller-controlled Host header.
        base_url = f'http://127.0.0.1:{self.server.server_port}'
        token = self.headers['Authorization']
        try:
            trips = trip_request(base_url, token)
            tools = make_trip_tools(base_url, token)
            reply = answer_chat(message, history, trips, tools)
            self.respond(200, {'reply': reply})
        except ValueError:
            self.respond(503, {'error': 'Chat is not configured. Check the backend AI settings.'})
        except ClientError as error:
            code = error.response['Error']['Code']
            if code in ('AccessDeniedException', 'UnrecognizedClientException', 'ExpiredTokenException'):
                message = 'Bedrock access is unavailable. Check your AWS login and model permissions.'
            else:
                message = 'Bedrock could not finish. Check your saved trips before retrying.'
            self.respond(503, {'error': message})
        except (BotoCoreError, GraphRecursionError, ToolException):
            self.respond(503, {'error': 'Chat could not finish. Check your saved trips before retrying.'})
