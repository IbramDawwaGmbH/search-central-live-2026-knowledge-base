"""The knowledge base's default visual style, read from _system/theme.yaml.

    from theme import default_style, pdf_style, STYLES
    default_style()            # 'art-deco' or 'deep-dive'
    pdf_style('deep-dive')     # 'ocean'  (the make_pdf.py style key)

theme.yaml holds one key, `default`, set to one of STYLES. Anything else stops with a ThemeError that names the file,
the bad value and the allowed values, so a typo never silently falls back to a style.
"""
from pathlib import Path

import yaml

__all__ = ['STYLES', 'PDF_STYLES', 'ThemeError', 'default_style', 'pdf_style']

HERE = Path(__file__).resolve().parent
THEME_FILE = HERE / 'theme.yaml'

STYLES = ('art-deco', 'deep-dive')
PDF_STYLES = {'art-deco': 'deco', 'deep-dive': 'ocean'}


class ThemeError(ValueError):
    """theme.yaml is missing, unreadable or names a style that does not exist."""


def default_style(path=THEME_FILE):
    """Return the default style from theme.yaml ('art-deco' or 'deep-dive'); raise ThemeError on a bad file or value."""
    path = Path(path)
    where = f'_system/{path.name}' if path.parent == HERE else str(path)
    try:
        data = yaml.safe_load(path.read_text(encoding='utf-8'))
    except FileNotFoundError:
        raise ThemeError(f'{where} is missing. Create it with one line: "default: deep-dive" (allowed: {", ".join(STYLES)}).') from None
    except yaml.YAMLError as e:
        raise ThemeError(f'{where} is not valid YAML: {e}') from None
    if not isinstance(data, dict) or 'default' not in data:
        raise ThemeError(f'{where} needs a "default:" key set to one of: {", ".join(STYLES)}.')
    value = data['default']
    if value not in STYLES:
        raise ThemeError(f'{where}: default is {value!r}, but it must be one of: {", ".join(STYLES)}.')
    return value


def pdf_style(name):
    """Map a theme style name to its make_pdf.py style key: art-deco -> deco, deep-dive -> ocean."""
    if name not in PDF_STYLES:
        raise ThemeError(f'unknown style {name!r}; allowed: {", ".join(STYLES)}.')
    return PDF_STYLES[name]


if __name__ == '__main__':
    s = default_style()
    print(f'{s} (PDF style: {pdf_style(s)})')
