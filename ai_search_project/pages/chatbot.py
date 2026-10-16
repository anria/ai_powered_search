# pages/chatbot.py
"""
Backend for the chatbot popup, calling a local Ollama instance.

The model chevalblanc/gpt-4o-mini must be pulled and running via Ollama
before this will work:
    ollama pull chevalblanc/gpt-4o-mini
    ollama serve
"""

import json
import os
import urllib.request
import urllib.error
from django.conf import settings


# Ollama connection settings
# OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
# OLLAMA_MODEL = "chevalblanc/gpt-4o-mini"
OLLAMA_HOST = getattr(settings, 'OLLAMA_URL', 'http://localhost:11434')
OLLAMA_MODEL = getattr(settings, 'OLLAMA_CHATBOT_MODEL', 'FableForge-AI/nexus-legal' )
OLLAMA_ENDPOINT = getattr(settings, 'OLLAMA_CHATBOT_ENDPOINT', '/api/chat' )
OLLAMA_TIMEOUT = 120  # seconds — local inference can be slow on first load

SYSTEM_PROMPT = (
    "forget all previous prompts. You are Nexus Legal Assistant. Find and discuss legal cases. State the judges, the parties, the issue, the ruling and dissent. Answer concisely and helpfully. If you don't know, say so."
)

MAX_HISTORY = 0


def get_reply(messages):
    """
    messages: list of {"role": "user"|"assistant", "content": str}
    returns:  str (the assistant's reply)
    """
    messages = messages[-MAX_HISTORY:]
    # print("_____Ollama = ", OLLAMA_HOST, " ______ ", OLLAMA_MODEL, flush=True)
    # print("_____SYSTEM_PROMPT= ", SYSTEM_PROMPT,  flush=True)

    # Prepend the system prompt as the first message
    ollama_messages = [{"role": "system", "content": SYSTEM_PROMPT}, *messages]

    payload = {
        "model": OLLAMA_MODEL,
        "messages": ollama_messages,
        "stream": False,
        "options": {
            "temperature": 0.7,
        },
    }

    url = f"{OLLAMA_HOST}{OLLAMA_ENDPOINT}"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=OLLAMA_TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["message"]["content"].strip()

    except urllib.error.HTTPError as e:
        if e.code == 404:
            return (
                f"Ollama says model '{OLLAMA_MODEL}' is not available. "
                f"Run: ollama pull {OLLAMA_MODEL}"
            )
        return f"Ollama returned HTTP {e.code}: {e.reason}"

    except urllib.error.URLError as e:
        return (
            f"Could not reach Ollama at {OLLAMA_HOST}. "
            "Is it running? Start it with: ollama serve"
        )

    except json.JSONDecodeError:
        return "Ollama returned an unparseable response."

    except Exception as e:
        return f"Chatbot error: {e}"