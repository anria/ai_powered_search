from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse

import json
from pathlib import Path
from typing import Any, Union
from django.conf import settings
from typing import Any, Optional

import requests
from django.shortcuts import render
from django.conf import settings


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
SOLR_URL = getattr(settings, 'SOLR_URL', 'http://localhost:8983/solr/ai_search/query')
SOLR_ROWS = 5   # how many results to fetch
print( "SOLR_URL", SOLR_URL )

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

def search(request):
    query = request.GET.get('q', '').strip()
    results = []
    error = None
    num_found = 0

    if query:
        params = {
            'q': query,
        }
        print("params", params)
        try:
            resp = requests.get(SOLR_URL, params=params, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            print("data.len", len(data))
            solr_docs = data.get('response', {}).get('docs', [])
            num_found = data.get('response', {}).get('numFound', 0)

            for doc in solr_docs:
                # Adjust these field names to match your Solr schema
                results.append({
                    'id':       doc.get('id'),
                    'title':    doc.get('title', doc.get('id', 'Untitled')),
                    'snippet':  doc.get('content', '')[:200],  # simple truncation
                    'score':    doc.get('score'),
                    'chapter':  doc.get('chapter'),  # if you store a chapter number
                })
        except requests.exceptions.RequestException as e:
            error = f"Could not reach Solr at {SOLR_URL}: {e}"
        except ValueError:
            error = "Solr returned a non-JSON response."

    return render(request, 'search_results.html', {
        'results':   results,
        'query':     query,
        'error':     error,
        'num_found': num_found,
    })