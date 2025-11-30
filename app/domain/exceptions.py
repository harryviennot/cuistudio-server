"""
Custom exceptions for domain-specific errors
"""


class NotARecipeError(Exception):
    """Raised when content is determined to not be a recipe"""

    def __init__(self, message: str = "Content does not appear to be a recipe"):
        self.message = message
        super().__init__(self.message)


class WebsiteBlockedError(Exception):
    """
    Raised when a website blocks automated extraction (403 Forbidden).
    Users should be directed to use manual paste method instead.
    """

    def __init__(self, url: str, message: str = "Website blocks automated extraction"):
        self.url = url
        self.message = message
        super().__init__(self.message)
