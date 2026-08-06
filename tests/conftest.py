import pytest
from core.config import settings

# Force TESTING setting to True so database calls fallback to in-memory dictionaries during test suite run
settings.TESTING = True
