"""Module kagtcprlib is a module for interfacing with the game
King Arthur's Gold over a TCP RCON connection.

Submodules
==========

.. autosummary::
    :toctree: _autosummary

    client
    constants
    exceptions
    handlers
    utils
    opt
"""
from .client import * # pylint: disable=wildcard-import
