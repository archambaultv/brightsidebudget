from typing import Any, Iterable


class HasTags():
    """
    A mixin class to add tags
    """
    def __init__(self, tags: dict[str, Any] | None = None):
        self.tags = tags or {}


def clean_tags(tags: dict[str, Any], forbidden: list[str] = None, err_ctx: str = ""):
    """
    Remove empty tags from a dictionary.
    """
    if forbidden is None:
        forbidden = []

    for x in forbidden:
        tags.pop(x, None)
    for k, v in list(tags.items()):
        if v is None or (isinstance(v, str) and v.strip() == ""):
            tags.pop(k)
        if isinstance(v, list):
            msg = "Extra columns"
            if err_ctx:
                msg = f"{err_ctx}: {msg}"
            raise ValueError(msg)


def all_tags(ls: Iterable[HasTags]) -> list[str]:
    """
    Returns a list of all tags used in the balance assertions.
    """
    return sorted({k for b in ls for k in b.tags.keys()})
