from __future__ import annotations
from typing import List
from jinja2 import Template
from assistant.utils.dto import PriceSnapshot, VixClose, CpiRelease, PaperItem

TPL_MD = Template("""\
# Daily Quant Digest — {{ date }}

## Market Summary
{% if quotes %}
{% for q in quotes -%}
- {{ q.symbol }}: {{ "%.2f"|format(q.price) }} (as of {{ q.as_of }})
{% endfor %}
{% else -%}
_No market quotes available for today._
{% endif %}

## VIX (FRED)
- {{ vix.date }} close: {{ "%.2f"|format(vix.close) }}

## Upcoming CPI (BLS)
{% if cpi %}
{% for r in cpi[:3] -%}
- {{ r.date }} {{ r.time_et }} ET{% if r.url %} — {{ r.url }}{% endif %}
{% endfor %}
{% else %}
_No upcoming CPI releases found._
{% endif %}

## Papers — arXiv (q-fin)
{% if arxiv %}
{% for p in arxiv[:6] -%}
- {{ p.title }}{% if p.year %} ({{ p.year }}){% endif %}{% if p.authors %} — {{ ", ".join(p.authors) }}{% endif %} — {{ p.url }}
{% endfor %}
{% else %}
No new papers found today
{% endif %}

## Papers — Semantic Scholar
{% if s2 %}
{% for p in s2[:6] -%}
- {{ p.title }}{% if p.year %} ({{ p.year }}){% endif %}{% if p.authors %} — {{ ", ".join(p.authors) }}{% endif %} — {{ p.url }}
{% endfor %}
{% else %}
No new papers found today
{% endif %}
""")


def render_digest(
    date: str,
    quotes: List[PriceSnapshot],
    vix: VixClose,
    cpi: List[CpiRelease],
    arxiv: List[PaperItem],
    s2: List[PaperItem],
) -> str:
    # IMPORTANT: pass "arxiv" (lowercase) to match the template
    return TPL_MD.render(date=date, quotes=quotes, vix=vix, cpi=cpi, arxiv=arxiv, s2=s2)
