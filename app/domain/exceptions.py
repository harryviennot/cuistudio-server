"""
Custom exceptions for domain-specific errors
"""


class NotARecipeError(Exception):
    """Raised when content is determined to not be a recipe"""

    def __init__(self, message: str = "Content does not appear to be a recipe"):
        self.message = message
        super().__init__(self.message)
