from abc import ABC, abstractmethod
from typing import Any


class WebToolAdapter(ABC):
    """Abstract base class for web framework adapters.

    Subclasses implement get_urls() to return framework-specific URL/route
    definitions for all tools registered in WEB_TOOL_REGISTRY, and
    make_view() to wrap a tool function in a framework-specific request handler.

    Usage:
        adapter = DjangoAdapter()
        urlpatterns = adapter.get_urls()
    """

    @abstractmethod
    def get_urls(self) -> Any:
        """Return URL patterns/routes for all registered web tools.

        Returns a framework-specific collection of URL patterns
        (e.g. a list of Django path() objects, or a Flask Blueprint).
        """
        pass

    @abstractmethod
    def make_view(self, name: str, fn: callable) -> Any:
        """Wrap a tool function in a framework-specific request handler.

        Args:
            name: The registered tool name.
            fn: The tool function to expose.

        Returns:
            A callable suitable as a view/handler in the target framework.
        """
        pass
