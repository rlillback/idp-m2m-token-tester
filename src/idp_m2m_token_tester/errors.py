class TokenTesterError(Exception):
    """Base class for expected, user-facing errors."""


class ConfigError(TokenTesterError):
    """A required setting is missing or invalid."""


class TokenRequestError(TokenTesterError):
    """The IdP rejected the request or could not be reached."""


class VerificationError(TokenTesterError):
    """Signature verification was requested but failed."""
