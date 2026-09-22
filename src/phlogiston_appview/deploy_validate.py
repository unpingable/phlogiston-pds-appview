"""Immutable local container-image admission for the synthetic compose helper."""

import re

IMMUTABLE = re.compile(r"^[^@/:\s]+(?:/[^@/:\s]+)+@sha256:[0-9a-f]{64}$")


def validate_image(image: str) -> str:
    if not IMMUTABLE.fullmatch(image):
        raise ValueError("image must be an untagged registry/repository image@sha256:<64 lowercase hex>")
    return image
