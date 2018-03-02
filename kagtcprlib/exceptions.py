"""Module exceptions contains any custom Exceptions which the library might raise.
"""

class NotConnectedException(Exception):
    """Raised when a send is attempted on a client that isn't connected yet.
    """
    pass
