def dimensions(height_mm: int, width_mm: int) -> str:
    return f"{_cm(height_mm)} × {_cm(width_mm)} cm"


def _cm(mm: int) -> str:
    cm, rest = divmod(mm, 10)
    return f"{cm}.{rest}" if rest else str(cm)
