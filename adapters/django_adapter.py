"""Django adapter for agent_toolbelt web tools.

Dynamically generates Django URL patterns for all tools registered with
@register_webtool. Each tool is exposed as a POST endpoint at /tools/{name}/.

Usage in your Django urls.py:
    from agent_toolbelt.adapters.django_adapter import DjangoAdapter
    from agent_toolbelt.framework import WEB_TOOL_REGISTRY
    import chatlib  # ensure tools are registered via @register_webtool

    adapter = DjangoAdapter()
    urlpatterns = [
        path('api/', include(adapter.get_urls())),
    ]
"""
import json
from typing import Any

from .base import WebToolAdapter
from agent_toolbelt.framework import WEB_TOOL_REGISTRY


class DjangoAdapter(WebToolAdapter):
    """Generates Django URL patterns for all @register_webtool-decorated functions.

    Each tool is exposed as a POST endpoint accepting a JSON body,
    and also as a GET endpoint using query parameters. Responses are JSON.
    """

    def make_view(self, name: str, fn: callable) -> Any:
        """Create a Django view function for the given tool."""
        # Lazy import so Django isn't required at module load time
        from django.http import JsonResponse
        from django.views.decorators.csrf import csrf_exempt
        from django.views.decorators.http import require_http_methods

        @csrf_exempt
        @require_http_methods(["GET", "POST"])
        def tool_view(request):
            try:
                if request.method == "POST":
                    body = json.loads(request.body or "{}")
                else:
                    body = dict(request.GET)
                    # Flatten single-value lists from QueryDict
                    body = {k: v[0] if isinstance(v, list) and len(v) == 1 else v
                            for k, v in body.items()}
                result = fn(**body)
                return JsonResponse({"result": result})
            except TypeError as e:
                return JsonResponse({"error": f"Invalid arguments: {e}"}, status=400)
            except Exception as e:
                return JsonResponse({"error": str(e)}, status=500)

        tool_view.__name__ = f"tool_{name}"
        return tool_view

    def get_urls(self) -> list:
        """Return a list of Django URL patterns for all registered web tools."""
        from django.urls import path

        return [
            path(f"tools/{name}/", self.make_view(name, fn), name=f"tool_{name}")
            for name, fn in WEB_TOOL_REGISTRY.items()
        ]
