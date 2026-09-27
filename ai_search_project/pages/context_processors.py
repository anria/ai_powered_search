from django.conf import settings

def chatbot_config(request):
    config = {
        "CHATBOT_CONFIG": {
            "ollama_host": getattr(settings, "OLLAMA_URL", "http://localhost:11434"),
            "ollama_model": getattr(settings, "OLLAMA_CHATBOT_MODEL", "FableForge-AI/nexus-legal"),
            "chat_endpoint": "/api/chat",
            "timeout_ms": getattr(settings, "CHATBOT_TIMEOUT_MS", 180000),
        }
    }
    return config