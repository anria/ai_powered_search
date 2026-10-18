from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.shortcuts import render
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect

from .feedback import (
    append as fb_append,
    load_all as fb_load_all,
    update_approved as fb_update,
    update_notes as fb_update_notes,   # <-- new 10/17/2026
)

import json
from pathlib import Path
from typing import Any, Union
from django.conf import settings
from typing import Any, Optional


import requests
import numpy as np
import time
import orjson
import ollama
from ollama import Client 

from .chatbot import get_reply

# Placeholder content for 15 chapters (you can replace with database models)
# usage: 'content': CHAPTERS[chapter_id],


# ---- Solr-backed search ----
SOLR_URL = getattr(settings, 'SOLR_URL', 'http://10.4.0.5:8983/solr/ai_search/query')
SOLR_ROWS = getattr(settings, 'SOLR_ROWS', 5)   # how many results to fetch
# print( "_____ views.py --> SOLR_URL", SOLR_URL )

OLLAMA_URL = getattr(settings, 'OLLAMA_URL', 'http://localhost:11434/api/embed')
OLLAMA_EMBED_MODEL = getattr(settings, 'OLLAMA_EMBED_MODEL', 'hf.co/ggml-org/e5-small-v2-Q8_0-GGUF:Q8_0' )
OLLAMA_CHATBOT_MODEL = getattr(settings, 'OLLAMA_CHATBOT_MODEL', 'FableForge-AI/nexus-legal' )


def read_json_file(file_path: Union[str, Path], relative_to_base: bool = True) -> Any:
    """
    Read a JSON file from disk in a Django project.
    Args:
        file_path: Path to the JSON file.
                   - If relative_to_base=True (default), the path is relative to settings.BASE_DIR
                   - If relative_to_base=False, the path is treated as absolute or relative to CWD
        relative_to_base: Whether to resolve the path relative to Django's BASE_DIR

    Returns:
        The parsed JSON content (dict, list, etc.)

    Raises:
        FileNotFoundError: If the file does not exist
        json.JSONDecodeError: If the file contains invalid JSON
        OSError: For other file-related errors
    """
    # Example usage:
    # data = read_json_file("data/chapters.json")               # relative to BASE_DIR
    # data = read_json_file("/absolute/path/to/file.json", relative_to_base=False)

    path = Path(file_path)

    if relative_to_base and not path.is_absolute():
        path = Path(settings.BASE_DIR) / path

    with path.open(mode="r", encoding="utf-8") as f:
        return json.load(f)

def get_chapters(data):
    chapters = []
    for chapter in data:
        if chapter.get("chapter") != 0:
            chapters.append( chapter.get('chapter') ) 
            
    return list(chapters)

CONTENTS = read_json_file("data/chapters_original.json")
CHAPTERS = get_chapters(CONTENTS)


def get_chapter(data: list[dict[str, Any]], chapter_number: int = 5) -> Optional[str]:
    """
    Extract the title of a specific chapter from the JSON data.
    
    Args:
        data: List of chapter objects loaded from the JSON file
        chapter_number: The chapter number to look up (default: 7)
        
    Returns:
        The chapter title as a string, or None if the chapter is not found
    """
    for chapter in data:
        if chapter.get("chapter") == chapter_number:
            # return chapter.get("title")
            return chapter
    return None

def index(request):
    return render(request, 'index.html')

def chapter(request, chapter_id):
    # Ensure chapter exists
    if chapter_id not in CHAPTERS:
        # could return 404
        return render(request, '404.html', status=404)
    CHAPTER_DATA = get_chapter(CONTENTS, chapter_id)
    context = {
        'chapter_id': chapter_id,
        'content': CHAPTER_DATA,
        'chapters_range': range(5, 16),  # for dropdown
        'previous_id': chapter_id - 1 if chapter_id > 5 else None,
        'next_id': chapter_id + 1 if chapter_id < 15 else None,
    }
    return render(request, 'chapter.html', context)


def get_embeddings(text_input, dimension):
    print("______ Ollama ", OLLAMA_URL, " \nMODEL ", OLLAMA_EMBED_MODEL, flush=True) 
    embed_model = OLLAMA_EMBED_MODEL
    endpoint = "/api/embed"
    payload = {
        "model": embed_model,
        "input": text_input,
        "stream": False
    }

    start = time.perf_counter()
    response = requests.post(OLLAMA_URL+endpoint, json=payload, timeout=3, headers={'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8'})
    
    full_embedding = orjson.loads(response.content)
    end = time.perf_counter()
    
    if "embeddings" in full_embedding:
        truncated_vector = np.array(full_embedding["embeddings"][0][:dimension])
        normalized_vector = truncated_vector / np.linalg.norm(truncated_vector)
        full_embedding = normalized_vector
    elif "error" in full_embedding:
        print("_____ Embedding Error", full_embedding, flush=True)
        full_embedding = []

    return full_embedding.tolist()  

def get_ai_chat(text_input):
    # NOT USED -- but keep this for now for the format
    embed_model = OLLAMA_CHATBOT_MODEL
    payload = {
        "model": embed_model,
        "messages": [
        {
          "role": "system",
          "content": "forget all previous prompts. You are a domain-specialized AI assistant for legal review. Respond in 4 short sentences. If asked, note the parties, the judge, the issue and the ruling and if available, the dissenting judge and opinion in list format."
        },
        {
          "role": "user",
          "content": text_input
        }
        ],
        "stream": False,
        "format": {
            "type": "object",
            "properties": {
              "judge_ruling": { "type": "string" },
              "parties": { "type": "string" },
              "issue": { "type": "string"},
              "dissenting_opinion": { "type": "string" }
            },
            "required": ["judge_ruling", "parties",  "issue", "dissenting_opinion"]
          }
    }
    url = OLLAMA_URL.replace("embed", "chat")
    try:
        response = requests.post(url, json=payload, timeout=30, headers={'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8'})
        response.raise_for_status()
        full_response =  orjson.loads(response.content)

        if "error" in full_response:
            message = full_response["error"]
        if "message" in full_response:
            message = full_response["message"]

    except requests.exceptions.ReadTimeout:
        print("Error: The server did not send data within the allocated read timeout period.", flush=True)
        message = {"error": "Error: The server did not send data within the allocated read timeout period."}
    except requests.exceptions.ConnectTimeout:
        print("Error: Could not establish a connection to the server.", flush=True)
        message = {"error": "Error: Could not establish a connection to the server."}

    return message




def extract_relationships(text, lang_model, coref_model):
    resolved_text = resolve_coreferences(text, coref_model)
    sentences = get_sentences(resolved_text, lang_model)
    return resolve_facts(sentences, lang_model)

def chapter5_get_query(origQueryJson):
    # pip3 install spacy
    # pip3 install spacy-experimental
    # pip3 install spacy spacy-transformers
    # python3 -m spacy download en_core_web_sm
    # python3 -m spacy download en_core_web_trf
    stopwords = ["i", "me", "my", "myself", "we", "you", "he", "she", "it", "they","a", "an", "the", "in", "on", "at", "by", "for", "with", "about", "against", "and", "but", "or", "because", "as", "until", "while", "is", "am", "are", "was", "were"]

    qList = origQueryJson["q"].split(" ")
    query = ""
    print("1. LEN(qlist)", len(qList), flush=True)
    for q in qList:
        if q not in stopwords:
            origQueryJson["facet.query"] = q


    print("2. LEN(qlist)", len(qList), flush=True)
    print("___ qList", qList, flush=True)
    for q in qList:
        origQueryJson["facet.query"] = q

    return origQueryJson


def search(request):
    query = request.GET.get('q', '').strip()
    chapter_id = request.GET.get('chapter_id', '').strip()
    print("_____ saerch --> chapter_id ", chapter_id, flush=True)
    results = []
    error = None
    num_found = 0
    qTime = 0
    chapter_reqHandlers = [7,13]
    template = 'search_results.html'


    CHAPTER_SOLR_URL = SOLR_URL
    if int(chapter_id) in chapter_reqHandlers:
        CHAPTER_SOLR_URL = SOLR_URL.replace("query", "chapter" + chapter_id)

    if query:
        params = {
            'q': query,
        }
        match int(chapter_id):
            case 5:
                params = chapter5_get_query(params)

            case 13:
                vector = get_embeddings(query, 50)
                if isinstance(vector, list) and len(vector) >=1 :
                    params["q"] = "{!knn f=dv_general_text topK=10}" + str(vector).replace(" ", "")
                    params["hl"] = "false"
                    CHAPTER_SOLR_URL = SOLR_URL #.replace("query", "search")

        try:
            resp = requests.get(CHAPTER_SOLR_URL, params=params, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            qTime      = data.get('responseHeader', {}).get('QTime', 0)
            solr_docs  = data.get('response', {}).get('docs', [])
            num_found  = data.get('response', {}).get('numFound', 0)
            highlights = data.get('highlighting', {})

            for doc in solr_docs:
                highlight = "<span class='collapsable-content'>"

                if doc.get('id') in highlights:
                    if 'text' in highlights.get(doc.get('id')):
                        highlight += "<b><u>Text:</u></b> " + highlights.get(doc.get('id')).get('text')[0] 
                    if 'judge_ruling' in highlights.get(doc.get('id')):
                        highlight += "<br><b><u>Judge_ruling:</u></b> " + highlights.get(doc.get('id')).get('judge_ruling')[0]
                highlight += "</span>"
                # Adjust these field names to match your Solr schema
                results.append({
                    'id':  doc.get('docket_number'),
                    'hl': highlight,
                    'title': '<a href="'+ doc.get('url') + '" target="_blank">' + doc.get('title', doc.get('case_name', 'Untitled')) +'</a>',
                    'snippet':  '<b>Date:</b> ' + doc.get('case_date')[:10] + '<br><b>Court:</b> ' +  doc.get('court_name'),
                    'score':    doc.get('score'),
                    
                    # 'chapter':  doc.get('chapter'),  # if you store a chapter number
                })
        except requests.exceptions.RequestException as e:
            error = f"Could not reach Solr at {CHAPTER_SOLR_URL}: {e}"
        except ValueError:
            error = "Solr returned a non-JSON response."

    return render(request, template, {
        'results':   results,
        'query':     query,
        'chapter_id': chapter_id,
        'error':     error,
        'qTime': qTime,
        'num_found': num_found,
    })



@require_POST
@csrf_protect
def chat(request):
    print("_____ inside views > chat")
    try:
        body = json.loads(request.body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    messages = body.get("messages", [])
    if not isinstance(messages, list) or not messages:
        return JsonResponse({"error": "messages must be a non-empty list"}, status=400)

    # Basic sanitisation: each item must be a dict with role + content strings
    clean = []
    for m in messages[-12:]:
        if (isinstance(m, dict)
                and m.get("role") in ("user", "assistant")
                and isinstance(m.get("content"), str)):
            clean.append({"role": m["role"], "content": m["content"][:4000]})

    if not clean:
        return JsonResponse({"error": "No valid messages"}, status=400)

    try:
        print("____GOING TO TRY TRY TRY ")
        reply = get_reply(clean)
        print("____DONE TO TRY TRY TRY ", reply, flush=True)

    except Exception as e:
        print("____ CHAT Exception ", e)
        return JsonResponse({"error": f"Server error: {e}"}, status=500)

    return JsonResponse({"reply": reply})    


@require_POST
@csrf_protect
def feedback(request):
    """Record a thumbs up/down on an assistant answer."""
    try:
        body = json.loads(request.body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    prompt    = str(body.get("prompt", ""))[:4000]
    answer    = str(body.get("answer", ""))[:20000]
    judgement = body.get("judgement")
    notes     = str(body.get("notes", ""))[:4000]   # <-- new

    if judgement not in (0, 1):
        return JsonResponse({"error": "judgement must be 0 or 1"}, status=400)
    if not prompt or not answer:
        return JsonResponse({"error": "prompt and answer are required"}, status=400)

    try:
        record = fb_append(prompt, answer, judgement, notes)
    except Exception as e:
        return JsonResponse({"error": f"Could not save feedback: {e}"}, status=500)

    return JsonResponse({"ok": True, "record": record})


def judgements(request):
    """Admin page listing all assistant responses."""
    return render(request, "judgements.html")


def judgements_data(request):
    """JSON feed for the judgements page."""
    return JsonResponse({"items": fb_load_all()})


@require_POST
@csrf_protect
def judgement_update(request, idx):
    """Approve or reject a record at index `idx`."""
    try:
        body = json.loads(request.body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    approved = body.get("approved")
    if approved not in (True, False):
        return JsonResponse({"error": "approved must be true or false"}, status=400)

    record = fb_update(idx, approved)
    if record is None:
        return JsonResponse({"error": "index out of range"}, status=404)
    return JsonResponse({"ok": True, "record": record})    


@require_POST
@csrf_protect
def judgement_notes(request, idx):
    """Update the notes field on a record."""
    try:
        body = json.loads(request.body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    notes = str(body.get("notes", ""))[:4000]
    record = fb_update_notes(idx, notes)
    if record is None:
        return JsonResponse({"error": "index out of range"}, status=404)
    return JsonResponse({"ok": True, "record": record})    