"""
==============================================================================
Models Package Initialization
==============================================================================
This file makes the models directory a Python package and exports
the main database instance and models.
"""

from .interaction import db, HCP, Interaction

__all__ = ['db', 'HCP', 'Interaction']