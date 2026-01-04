from datetime import datetime
from typing import Any, Dict, Optional

class BaseModel:
    """Base class for all models, providing common attributes and methods."""

    def __init__(self, id: Optional[int] = None,
                 creation_timestamp: Optional[str] = None,
                 modification_timestamp: Optional[str] = None):
        self.id = id
        self.creation_timestamp = creation_timestamp if creation_timestamp else datetime.now().isoformat()
        self.modification_timestamp = modification_timestamp if modification_timestamp else datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Converts the model instance to a dictionary."""
        return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={self.id})>"

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.id == other.id and self.to_dict() == other.to_dict()