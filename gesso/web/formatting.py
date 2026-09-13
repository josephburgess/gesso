import re
def dimensions(height_mm: int, width_mm: int) -> str:
    return f'{_cm(height_mm)} × {_cm(width_mm)} cm'


def _cm(mm: int) -> str:
    cm, rest = divmod(mm, 10)
    return f'{cm}.{rest}' if rest else str(cm)


def price(pence: int) -> str:
    pounds, rest = divmod(pence, 100)
    return f'£{pounds:,}' + (f'.{rest:02d}' if rest else '')

def paragraphs(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
