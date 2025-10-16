from __future__ import annotations
from typing import List
from jinja2 import Template
from assistant.utils.dto import PriceSnapshot, VixClose, CpiRelease, PaperItem

TPL_MD = Template("""# Daily Quant Digest — {{ date }}
## Market Summary
{% for q in quotes %}- {{ q.symbol }}: {{ "%.2f"|format(q.price) }} (as of {{ q.as_of }})
{% endfor %}
## VIX (FRED)
- {{ vix.date }} close: {{ "%.2f"|format(vix.close) }}
## Upcoming CPI (BLS)
{% for r in cpi[:3] %}- {{ r.date }} {{ r.time_et }} ET{% if r.url %} — {{ r.url }}{% endif %}
{% endfor %}
## Papers — arXiv
{% for p in arxiv[:6] %}- {{ p.title }}{% if p.year %} ({{ p.year }}){% endif %} — {{ p.url }}
{% endfor %}
## Papers — Semantic Scholar
{% for p in s2[:6] %}- {{ p.title }}{% if p.year %} ({{ p.year }}){% endif %} — {{ p.url }}
{% endfor %}
""")

def render_digest(date:str, quotes:List[PriceSnapshot], vix:VixClose, cpi:List[CpiRelease], arxiv:List[PaperItem], s2:List[PaperItem])->str:
    return TPL_MD.render(date=date, quotes=quotes, vix=vix, cpi=cpi, arXiv=arxiv, s2=s2)
