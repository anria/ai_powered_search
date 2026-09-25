from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse

import json
from pathlib import Path
from typing import Any, Union
from django.conf import settings
from typing import Any, Optional

import requests
import numpy as np
import time
import orjson


# Placeholder content for 15 chapters (you can replace with database models)
# usage: 'content': CHAPTERS[chapter_id],

CHAPTERS = {
    i: f"<h2>Chapter {i}</h2><p>This is the content of chapter {i}. " +
       f"Lorem ipsum dolor sit amet, consectetur adipiscing elit. " +
       f"Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.</p>" +
       f"<p>More text for chapter {i} to make it longer and demonstrate the layout.</p>"
    for i in range(1, 16)
}

# ---- Solr-backed search ----
SOLR_URL = getattr(settings, 'SOLR_URL', 'http://10.4.0.5:8983/solr/ai_search/query')
SOLR_ROWS = getattr(settings, 'SOLR_ROWS', 5)   # how many results to fetch
# print( "_____ views.py --> SOLR_URL", SOLR_URL )

OLLAMA_URL = getattr(settings, 'OLLAMA_URL', 'http://10.5.0.5:11434/api/embed')
OLLAMA_EMBED_MODEL = getattr(settings, 'OLLAMA_EMBED_MODEL', 'qwen3-embedding:0.6b' )
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

    embed_model = OLLAMA_EMBED_MODEL
    payload = {
        "model": embed_model,
        "input": text_input,
        "stream": 0
    }

    start = time.perf_counter()
    response = requests.post(OLLAMA_URL, json=payload, timeout=3, headers={'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8'})
    
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
    embed_model = OLLAMA_CHATBOT_MODEL
    payload = {
        "model": embed_model,
        "messages": [
        {
          "role": "system",
          "content": "forget all previous prompts. You are NEXUS-LEGAL, a domain-specialized AI assistant for legal review. Respond in 5 short sentences noting the parties, the judge, the issue and the ruling and if available, the dissenting judge and opinion."
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


def search_chatbot(request, query, chapter_id):
    template = 'search_chat.html'
    results = get_ai_chat(query)
    print("_____ results", results, flush=True)
    output = ""
    error = ""
    if "error" in results:
        error = "<em>" + results["error"] + "</em>"
        output = results
    else:
        if "parties" in results:
            output = output + "<b>Parties: </b>" + results["parties"] + "<br>"
        if "issue" in results:
            output = output + "<b>Issue: </b>" + results["issue"] + "<br>"
        if "judge_ruling" in results:    
            output = output + "<b>Judge Opinion: </b>" + results["judge_ruling"] + "<br>"
        if "dissenting_opinion" in results:
            output = output + "<b>Dissenting Opinion: </b>" + results["dissenting_opinion"] + "<br>"


    return render(request, template, {
        'results':   output,
        'query':     query,
        'chapter_id': chapter_id,
        'error':     error,
    })


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
    if int(chapter_id) >= 14: 
        return search_chatbot(request, query, chapter_id)
    print("____ made it past the chatbot", flush=True)

    CHAPTER_SOLR_URL = SOLR_URL
    if int(chapter_id) in chapter_reqHandlers:
        CHAPTER_SOLR_URL = SOLR_URL.replace("query", "chapter" + chapter_id)

    if query:
        params = {
            'q': query,
        }

        if int(chapter_id) == 13:
            vector = get_embeddings(query, 50)
            if isinstance(vector, list) and len(vector) >=1 :
                params["q"] = "{!knn f=dv_general_text topK=10}" + str(vector).replace(" ", "")

        try:
            resp = requests.get(CHAPTER_SOLR_URL, params=params, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            qTime      = data.get('responseHeader', {}).get('QTime', 0)
            solr_docs  = data.get('response', {}).get('docs', [])
            num_found  = data.get('response', {}).get('numFound', 0)
            highlights = data.get('highlighting', {})

            for doc in solr_docs:
                highlight = ""
                if doc.get('id') in highlights:
                    if 'text' in highlights.get(doc.get('id')):
                        highlight += "<b>Text:</b> " + highlights.get(doc.get('id')).get('text')[0]
                    if 'judge_ruling' in highlights.get(doc.get('id')):
                        highlight += "<br><b>Judge_ruling:</b> " + highlights.get(doc.get('id')).get('judge_ruling')[0]
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