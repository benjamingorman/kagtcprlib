"""This allows test code to import main project code whilst avoiding import path hell
"""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import kagtcprlib
