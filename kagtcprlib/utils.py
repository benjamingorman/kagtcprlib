"""Module utils contains utility functions which are re-usable throughout the project. 
"""
import re

USERNAME_REGEX = "[a-zA-Z0-9\-_]{1,20}"

def looks_like_chat_msg(line):
    """Checks whether a line looks like it is a chat message (minus the timestamp).
    An example chat message is:
        "<Joan of Arc> What's up"
    
    Args:
        line (str): The line in question

    Returns:
        bool: Whether or not the line looks like a chat message
    """
    # It's hard to do better than this because there are so many valid chat messages
    return len(line) > 0 and line[0] == "<" and ">" in line
