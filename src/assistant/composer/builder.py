# src/assistant/composer/builder.py
from __future__ import annotations
from pathlib import Path
from typing import Iterable, Sequence

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from assistant.utils.dto import CpiRelease, DigestContext, PaperItem, PriceSnapshot, VixClose
from assistant.utils.logging import logger


def _ensure_list(items: Iterable | None) -> list:
    return list(items) if items else []


def _resolve_context(
    *,
    context: DigestContext | None,
    date: str | None,
    quotes: Sequence[PriceSnapshot] | None,
    vix: VixClose | None,
    cpi: Sequence[CpiRelease] | None,
    arxiv: Sequence[PaperItem] | None,
    s2: Sequence[PaperItem] | None,
) -> DigestContext:
    if context is not None:
        return context
    if date is None or vix is None:
        raise ValueError("render_digest requires either a context or date and vix values")
    return DigestContext(
        date=date,
        quotes=_ensure_list(quotes),
        vix=vix,
        cpi=_ensure_list(cpi),
        arxiv=_ensure_list(arxiv),
        s2=_ensure_list(s2),
    )


def render_digest(
    *,
    context: DigestContext | None = None,
    date: str | None = None,
    quotes: Sequence[PriceSnapshot] | None = None,
    vix: VixClose | None = None,
    cpi: Sequence[CpiRelease] | None = None,
    arxiv: Sequence[PaperItem] | None = None,
    s2: Sequence[PaperItem] | None = None,
) -> str:
    """Render the digest markdown using a template and high-level inputs."""
    resolved = _resolve_context(
        context=context,
        date=date,
        quotes=quotes,
        vix=vix,
        cpi=cpi,
        arxiv=arxiv,
        s2=s2,
    )

    template_dir = Path(__file__).parent / "templates"
    env = Environment(loader=FileSystemLoader(template_dir), autoescape=False)

    try:
        template = env.get_template("digest.md.j2")
    except TemplateNotFound as exc:
        logger.error(f"Template not found: {exc}")
        return "Error: Template not found."

    return template.render(ctx=resolved)
