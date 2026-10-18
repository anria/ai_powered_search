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
import requests
from django.conf import settings

import ollama

# Ollama connection settings
OLLAMA_HOST     = getattr(settings, 'OLLAMA_URL', 'http://localhost:11434')
OLLAMA_MODEL    = getattr(settings, 'OLLAMA_CHATBOT_MODEL', 'granite3.1-moe:1b' )
OLLAMA_ENDPOINT = getattr(settings, 'OLLAMA_CHATBOT_ENDPOINT', '/api/chat' )
OLLAMA_TIMEOUT  = getattr(settings, 'OLLAMA_CHATBOT_TIMEOUT', 180000 )

  # seconds — local inference can be slow on first load

SYSTEM_PROMPT = (
    "forget all previous prompts. You are the Legal Assistant. Find and discuss legal cases. State the case name, year, court, judges, the parties, the issue, the ruling and dissent. Answer concisely and helpfully. If you do not know, say so. Do not answer any questions that are not legal related."
)

MAX_HISTORY = 0


def get_reply(messages):
    """
    messages: list of {"role": "user"|"assistant", "content": str}
    returns:  str (the assistant's reply)
    """
    messages = messages[-MAX_HISTORY:]

    # Prepend the system prompt as the first message
    ollama_messages = [{"role": "system", "content": SYSTEM_PROMPT}, *messages]

    payload = {
        "model": OLLAMA_MODEL,
        "messages": ollama_messages,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "num_ctx": 8192,
            "num_predict": 512,
            "top_k": 40,
            "top_p": 0.9,
            "seed": 42,
            "stop": ["<EOT>"],
            "repeat_penalty": 1.15
        }
    }

    url = f"{OLLAMA_HOST}{OLLAMA_ENDPOINT}"
    response = requests.post(url, json=payload)

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        resp = requests.post(url, json=payload, timeout=OLLAMA_TIMEOUT)
        data = resp.json()
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

