"""Custom exception classes for database operations."""


class DatabaseError(Exception):
    """Base database error."""
    pass


class ConnectionError(DatabaseError):
    """Database connection failed."""
    pass


class QueryError(DatabaseError):
    """Query execution failed."""
    pass


class IntegrityError(DatabaseError):
    """Data integrity constraint violated."""
    pass


class NotFoundError(DatabaseError):
    """Requested resource not found."""
    pass


class ValidationError(DatabaseError):
    """Data validation failed."""
    pass
