class NotFoundError(LookupError):
    """Raised when a requested domain entity does not exist."""


class ConflictError(ValueError):
    """Raised when a domain uniqueness or consistency rule is violated."""
