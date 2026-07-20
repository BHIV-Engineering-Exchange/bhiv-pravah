from abc import ABC, abstractmethod
from typing import Dict, Any, List


class BaseModule(ABC):
    """Base class for modules (non-agent workloads).

    Modules should implement `process(data, context)` and return a serializable
    dictionary representing the module's result payload (not the final CoreResponse).
    The gateway will normalize this output into a `CoreResponse`.
    """

    @abstractmethod
    def process(self, data: Dict[str, Any], context: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process incoming data and return a plain result dict."""
        raise NotImplementedError()

    def metadata(self) -> Dict[str, Any]:
        """Optional module metadata. Modules may override to provide name/version."""
        return {}
