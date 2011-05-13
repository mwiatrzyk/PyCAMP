class CampError(Exception):
    """Base aplication's exception class."""


class CampFilterError(CampError):
    """Base class for all exceptions related to ``camp.filter`` module and
    its submodules."""
