from django.http import HttpResponse

class SilenceChromeDevToolsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == '/.well-known/appspecific/com.chrome.devtools.json':
            return HttpResponse(status=204)  # Silently return No Content
        return self.get_response(request)