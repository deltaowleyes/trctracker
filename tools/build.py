#!/usr/bin/env python3
"""Build TRC Tracker (trctracker.ca) from the files in data/.

    python3 tools/build.py            # build every page
    python3 tools/build.py --check    # validate data only, write nothing

Inputs:  site.config.json, data/calls.json, data/news/*.json
Outputs: index.html, news/index.html, news/<id>/index.html, 404.html,
         feed.xml, sitemap.xml
Only the Python standard library is used.
"""
import datetime
import html
import json
import pathlib
import re
import shutil
import sys
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "site.config.json").read_text(encoding="utf-8"))
SITE = CONFIG["site_url"].rstrip("/")
NAME = CONFIG["site_name"]
HEADER = CONFIG.get("header_style", "A").upper()
ASSET_V = CONFIG.get("asset_version", "1")
AOS_HEAD = (f'<link rel="stylesheet" href="/assets/vendor/aos.css?v={ASSET_V}">\n'
            f'<script defer src="/assets/vendor/aos.js?v={ASSET_V}"></script>')

STATUS_ORDER = ["Complete", "In progress", "Stalled", "Not started"]
STATUS_CLASS = {"Complete": "complete", "In progress": "progress", "Stalled": "stalled", "Not started": "notstarted"}

TOPIC_CONTEXT = {
    "Child Welfare": "Residential schools separated children from families and communities. Today, child-welfare policy must be judged by family safety, cultural continuity and the outcomes experienced by Indigenous children.",
    "Education": "Education was used as a tool of assimilation in residential schools. These Calls seek equitable opportunities, culturally relevant learning and public accountability.",
    "Language and Culture": "Residential schools suppressed Indigenous languages and cultural transmission. Community-led revitalization depends on rights, resources and intergenerational teaching.",
    "Health": "Residential schools and colonial policies contributed to enduring health inequities. These Calls address access, recognition of rights and culturally safe services.",
    "Justice": "Colonial policies and residential school harms shape contemporary justice questions. These Calls ask institutions to address barriers, inequities and Indigenous legal traditions.",
    "Missing Children and Burial Sites": "Families and communities have sought records and answers about children who never returned from residential schools. Accuracy, consent and respectful stewardship are essential.",
    "Business": "Reconciliation also requires private-sector conduct that respects Indigenous rights and creates fair economic opportunities.",
}
DEFAULT_CONTEXT = "This recommendation is part of the TRC's response to the legacy of residential schools. Its importance lies in turning recognition of harms into institutional responsibilities and measurable change."


def esc(x):
    return html.escape(str(x), quote=True)


def long_date(iso):
    d = datetime.date.fromisoformat(iso)
    return d.strftime("%B ") + str(d.day) + d.strftime(", %Y")


def short_date(iso):
    d = datetime.date.fromisoformat(iso)
    return d.strftime("%b ") + str(d.day) + d.strftime(", %Y")


# ---------------------------------------------------------------- data
def load_calls():
    data = json.loads((ROOT / "data" / "calls.json").read_text(encoding="utf-8"))
    calls = data["calls"]
    assert [c["n"] for c in calls] == list(range(1, 95)), "calls.json must hold Calls 1-94 in order"
    for c in calls:
        assert c["status"] in STATUS_ORDER, f"Call {c['n']}: unknown status {c['status']}"
    return data


def https_url(u, where):
    p = urllib.parse.urlparse(u)
    if p.scheme != "https" or not p.hostname:
        raise ValueError(f"{where}: source URL must be https: {u}")


def load_news():
    items, seen = [], set()
    for path in sorted((ROOT / "data" / "news").glob("*.json")):
        d = json.loads(path.read_text(encoding="utf-8"))
        where = path.name
        for k in ("id", "date", "published", "headline", "sections", "sources"):
            if not d.get(k):
                raise ValueError(f"{where}: missing {k}")
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{2,100}", d["id"]):
            raise ValueError(f"{where}: id must be lower-case letters, digits and hyphens")
        if d["id"] in seen:
            raise ValueError(f"{where}: duplicate id {d['id']}")
        seen.add(d["id"])
        datetime.date.fromisoformat(d["date"])
        datetime.date.fromisoformat(d["published"])
        calls = d.get("calls", [])
        if not all(isinstance(n, int) and 1 <= n <= 94 for n in calls):
            raise ValueError(f"{where}: calls must be numbers 1-94")
        for s in d["sections"]:
            if not s.get("label") or not s.get("text"):
                raise ValueError(f"{where}: every section needs a label and text")
        for s in d["sources"]:
            if not s.get("title"):
                raise ValueError(f"{where}: every source needs a title")
            https_url(s.get("url", ""), where)
        if d.get("status", "published") != "published":
            continue
        items.append(d)
    items.sort(key=lambda x: (x["published"], x["date"], x["id"]), reverse=True)
    return items


# ---------------------------------------------------------------- shell
ICON_SEARCH = '<svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="M20 20l-4-4"/></svg>'
ICON_MENU = '<svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path class="i-open" d="M4 7h16M4 12h16M4 17h16"/><path class="i-close" d="M6 6l12 12M18 6L6 18"/></svg>'


def nav_links(active, cls):
    out = []
    for key, href, label, short in (("news", "/news/", "TRC News", "News"), ("calls", "/", "94 Calls to Action", "94 Calls")):
        cur = ' aria-current="page"' if key == active else ""
        out.append(f'<a class="{cls}" href="{href}"{cur}><span class="lbl-long">{label}</span><span class="lbl-short">{short}</span></a>')
    return "".join(out)


def search_link():
    return f'<a class="hdr-search" href="/#search" aria-label="Search the 94 Calls">{ICON_SEARCH}<span>Search Calls</span></a>'


def header(active, status_counts):
    if HEADER == "D":
        return f'''<header class="site-header hdr-d">
<div class="hdr-top">
<a class="hdr-badge" href="/" aria-label="{esc(NAME)} home"><img src="/assets/brand/badge-300.webp" alt="" width="132" height="132"></a>
<a class="hdr-word" href="/"><span class="w-main">TRC<span>Tracker</span><em>.ca</em></span><span class="w-tag">Tracking the 94 Calls to Action</span></a>
</div>
<a class="hdr-progress" href="/#status" aria-label="{status_counts['Complete']} of 94 Calls complete. See how status is assessed.">
<span class="hp-head"><b>{status_counts['Complete']} of 94 complete</b><small>Indigenous Watchdog, Oct 1, 2026</small></span>
</a>
</header>
<nav class="site-menu" data-sticky aria-label="Main">
<div class="menu-row">
<a class="menu-mark" href="/" aria-label="{esc(NAME)} home" tabindex="-1"><img src="/assets/brand/mark.webp" alt="" width="40" height="41"></a>
{nav_links(active, "menu-link")}
{search_link()}
</div>
</nav>'''
    if HEADER == "B":
        return f'''<header class="site-header hdr-b" data-sticky>
<div class="hdr-row">
<a class="hdr-badge" href="/" aria-label="{esc(NAME)} home"><img src="/assets/brand/badge-300.webp" alt="" width="112" height="112"></a>
<a class="hdr-word" href="/"><span class="w-main">TRC<span>Tracker</span>.ca</span><span class="w-tag">Tracking the 94 Calls to Action</span></a>
<nav class="hdr-nav" aria-label="Main">{nav_links(active, "hdr-tab")}{search_link()}</nav>
</div>
</header>'''
    if HEADER == "C":
        bar = "".join(f'<span class="seg {STATUS_CLASS[s]}" style="flex:{status_counts[s]}"></span>' for s in STATUS_ORDER)
        legend = "".join(f'<span class="lg"><i class="{STATUS_CLASS[s]}"></i>{status_counts[s]} {s.lower()}</span>' for s in STATUS_ORDER)
        return f'''<header class="site-header hdr-c" data-sticky>
<div class="hdr-row">
<a class="hdr-icon" href="/" aria-label="{esc(NAME)} home"><img src="/assets/brand/icon-192.png" alt="" width="52" height="52"></a>
<a class="hdr-word" href="/"><span class="w-main">TRC<span>Tracker</span>.ca</span><span class="w-tag">Tracking the 94 Calls to Action</span></a>
<nav class="hdr-nav" aria-label="Main"><span class="seg-ctl">{nav_links(active, "hdr-tab")}</span></nav>
{search_link()}
</div>
<a class="hdr-progress" href="/#status" aria-label="{status_counts['Complete']} of 94 Calls complete. See how status is assessed.">
<b>{status_counts['Complete']} of 94 complete</b><span class="bar" aria-hidden="true">{bar}</span><span class="legend" aria-hidden="true">{legend}</span><small>Indigenous Watchdog, Oct 1, 2026</small>
</a>
</header>'''
    # A: classic masthead with a phone drawer
    return f'''<header class="site-header hdr-a" data-sticky>
<div class="hdr-row">
<a class="hdr-logo" href="/"><img src="/assets/brand/logo-horizontal.webp" alt="TRCTracker.ca — Tracking the 94 Calls to Action" width="968" height="248"></a>
<button class="hdr-toggle" type="button" aria-expanded="false" aria-controls="site-nav" aria-label="Menu">{ICON_MENU}</button>
<nav class="hdr-nav" id="site-nav" aria-label="Main">{nav_links(active, "hdr-link")}{search_link()}</nav>
</div>
<div class="hdr-rule" aria-hidden="true"></div>
</header>'''


def page(*, title, description, path, active, body, status_counts, extra_head="", og_type="website"):
    canonical = SITE + path
    full_title = f"{title} | {NAME}" if title != NAME else NAME
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(full_title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{esc(canonical)}">
<meta property="og:site_name" content="{esc(NAME)}">
<meta property="og:type" content="{og_type}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{esc(canonical)}">
<meta property="og:image" content="{SITE}/assets/brand/og-image.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#A50F0F">
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" type="image/png" sizes="32x32" href="/assets/brand/icon-32.png">
<link rel="apple-touch-icon" href="/assets/brand/icon-180.png">
<link rel="manifest" href="/site.webmanifest">
<link rel="alternate" type="application/rss+xml" title="{esc(NAME)} — TRC News" href="/feed.xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Red+Hat+Display:ital,wght@0,700;0,800;0,900;1,700&display=swap">
<link rel="stylesheet" href="/assets/site.css?v={ASSET_V}">
<script defer src="/assets/site.js?v={ASSET_V}"></script>
{extra_head}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
{header(active, status_counts)}
<main id="main">
{body}
</main>
<footer class="site-footer">
<div class="ft-inner">
<p class="ft-brand"><img src="/assets/brand/mark.webp" alt="" width="48" height="49"> <span><b>{esc(NAME)}</b><br>Tracking the Truth and Reconciliation Commission of Canada's 94 Calls to Action.</span></p>
<nav class="ft-links" aria-label="Footer"><a href="/news/">TRC News</a><a href="/">94 Calls to Action</a><a href="/#status">How status is assessed</a><a href="/feed.xml">RSS feed</a></nav>
<p class="ft-src">Original Calls to Action: <a href="https://nctr.ca/about/truth-and-reconciliation-commission-of-canada-calls-to-action/">National Centre for Truth and Reconciliation</a>. Progress labels: <a href="https://www.indigenouswatchdog.org/">Indigenous Watchdog</a>. Summaries are plain-language, not the TRC's original wording.</p>
<p class="ft-copy">© {datetime.date.today().year} {esc(NAME)}</p>
</div>
</footer>
</body>
</html>
'''


# ---------------------------------------------------------------- calls page
def call_card(c, news_by_call, calls_by_topic, source):
    n = c["n"]
    status = c["status"]
    reqs = "".join(f"<li>{esc(r)}</li>" for r in c["requirements"])
    req_html = f"<ul>{reqs}</ul>" if reqs else '<p class="muted">A requirement-by-requirement breakdown has not been transcribed yet. Read the original wording at the NCTR (linked below) for the complete obligation.</p>'
    related = [m for m in calls_by_topic[c["topic"]] if m != n][:6]
    rel_html = ", ".join(f'<a href="#call-{m}">#{m}</a>' for m in related) or "None in this topic."
    news = news_by_call.get(n, [])[:5]
    news_html = ""
    if news:
        news_html = '<section><h4>Related TRC News</h4><ul class="rel-news">' + "".join(
            f'<li><a href="/news/{esc(x["id"])}/">{esc(x["headline"])}</a> <span class="muted">{short_date(x["published"])}</span></li>' for x in news) + "</ul></section>"
    owner = esc(c["responsible"]) if c["responsible"] else "To be verified against the original wording of this Call. Government, professional, religious, media and private-sector responsibilities differ across the 94 recommendations."
    search_blob = " ".join([str(n), c["title"], c["topic"], c["responsible"], *c["requirements"]]).lower()
    return f'''<article class="call" id="call-{n}" data-topic="{esc(c['topic'])}" data-status="{esc(status)}" data-search="{esc(search_blob)}">
<details>
<summary>
<span class="call-n">{n}</span>
<span class="call-main"><span class="call-title">{esc(c['title'])}</span><span class="call-topic">{esc(c['topic'])}</span></span>
<span class="pill {STATUS_CLASS[status]}">{esc(status)}</span>
</summary>
<div class="call-body">
<section><h4>What is required</h4>{req_html}</section>
<section><h4>Who must answer</h4><p>{owner}</p></section>
<section><h4>Independent progress status</h4><p><span class="pill {STATUS_CLASS[status]}">{esc(status)}</span> <span class="muted">According to {esc(source['name'])}, as of {long_date(source['as_of'])}. Not a TRC Tracker finding.</span></p></section>
<section><h4>Why this Call matters</h4><p>{esc(TOPIC_CONTEXT.get(c['topic'], DEFAULT_CONTEXT))}</p></section>
<section class="hard-truth"><h4>Hard truth</h4><p>{esc(c['hard_truth'])}</p><p class="muted">Editorial analysis: an accountability test, not a claim that every requirement remains unmet.</p></section>
<section><h4>Questions to ask</h4><p>Which exact requirements have been fulfilled? What dated documents show it? What outcomes are Indigenous communities reporting? What remains unfinished, and who is responsible for the next step?</p></section>
{news_html}
<section><h4>Related Calls</h4><p>{rel_html}</p></section>
<p class="call-links"><a href="https://www.indigenouswatchdog.org/cta/call-to-action-{n}/" rel="noopener">Evidence and chronology for Call #{n} (Indigenous Watchdog)</a><a href="https://nctr.ca/about/truth-and-reconciliation-commission-of-canada-calls-to-action/" rel="noopener">Original TRC wording (NCTR)</a><a href="#call-{n}" class="copy-link" data-call="{n}">Link to this Call</a></p>
</div>
</details>
</article>'''


def build_calls(calls_data, news, counts):
    calls = calls_data["calls"]
    source = calls_data["status_source"]
    news_by_call = {}
    for x in news:
        for n in x.get("calls", []):
            news_by_call.setdefault(n, []).append(x)
    calls_by_topic = {}
    for c in calls:
        calls_by_topic.setdefault(c["topic"], []).append(c["n"])
    topics = sorted(calls_by_topic)
    topic_opts = "".join(f'<option value="{esc(t)}">{esc(t)} ({len(calls_by_topic[t])})</option>' for t in topics)
    status_btns = "".join(f'<button type="button" class="chip" data-status="{esc(s)}" aria-pressed="false"><i class="{STATUS_CLASS[s]}"></i>{esc(s)} <b>{counts[s]}</b></button>' for s in STATUS_ORDER)
    bar = "".join(f'<span class="seg {STATUS_CLASS[s]}" style="flex:{counts[s]}" title="{counts[s]} {esc(s.lower())}"></span>' for s in STATUS_ORDER)
    groups = []
    for c in calls:
        if not groups or groups[-1][0] != c["topic"]:
            groups.append((c["topic"], []))
        groups[-1][1].append(c)
    parts = (("Legacy", "Calls 1–42: the harms of residential schools in child welfare, education, language, health and justice", lambda n: n <= 42),
             ("Reconciliation", "Calls 43–94: what governments, churches, institutions and Canadians must do next", lambda n: n >= 43))
    group_html = []
    first = True
    for pname, pdesc, inpart in parts:
        group_html.append(f'<div class="part"><h2 class="part-h">{pname}</h2><p class="part-d muted">{esc(pdesc)}</p></div>')
        for t, gc in groups:
            if not inpart(gc[0]["n"]):
                continue
            gcount = {s: sum(1 for c in gc if c["status"] == s) for s in STATUS_ORDER}
            gbar = "".join(f'<span class="seg {STATUS_CLASS[s]}" style="flex:{gcount[s]}"></span>' for s in STATUS_ORDER if gcount[s])
            rng = f"Call {gc[0]['n']}" if len(gc) == 1 else f"Calls {gc[0]['n']}–{gc[-1]['n']}"
            stalled = f'<span class="g-stalled">{gcount["Stalled"]} stalled</span>' if gcount["Stalled"] else ""
            label = f'{gcount["Complete"]} of {len(gc)} complete' + (f', {gcount["Stalled"]} stalled' if gcount["Stalled"] else "")
            cards = "\n".join(call_card(c, news_by_call, calls_by_topic, source) for c in gc)
            group_html.append(f'''<details class="group" data-topic="{esc(t)}" data-aos="fade-up"{" open" if first else ""}>
<summary><span class="g-name"><b>{esc(t)}</b><small>{rng}</small></span><span class="g-stat"><span class="bar mini" role="img" aria-label="{esc(label)}">{gbar}</span><span class="g-count">{gcount["Complete"]} of {len(gc)} complete</span>{stalled}</span></summary>
<div class="g-calls">
{cards}
</div>
</details>''')
            first = False
    cards = "\n".join(group_html)
    strip = "".join(f'''<article class="ns-card" data-aos="fade-up" data-aos-delay="{i * 100}">
<p class="meta"><time datetime="{x['published']}">{short_date(x['published'])}</time>{"".join(f'<a class="tag" href="/#call-{n}">Call #{n}</a>' for n in x.get("calls", [])[:2])}</p>
<h3><a href="/news/{esc(x['id'])}/">{esc(x['headline'])}</a></h3>
</article>''' for i, x in enumerate(news[:3]))
    hero = CONFIG.get("hero_image", "")
    if hero:
        credit = f'<figcaption>{esc(CONFIG.get("hero_credit", ""))}</figcaption>' if CONFIG.get("hero_credit") else ""
        art = f'<figure class="hero-art"><img src="{esc(hero)}" alt="{esc(CONFIG.get("hero_alt", ""))}" width="720" height="540" fetchpriority="high">{credit}</figure>'
    else:
        art = "<!-- hero art slot: set hero_image, hero_alt and hero_credit in site.config.json and rebuild -->"
    body = f'''<section class="page-head{' has-art' if hero else ''}">
<div class="ph-text">
<p class="eyebrow">Directory</p>
<h1>94 Calls to Action</h1>
<p class="lede">Plain-language summaries of every Call from the Truth and Reconciliation Commission of Canada, who is responsible, and where each one stands.</p>
</div>
{art}
</section>
<section class="status-panel" id="status" aria-labelledby="status-h">
<div class="sp-top"><h2 id="status-h">{counts['Complete']} of 94 complete</h2><p class="muted">Independent assessment by {esc(source['name'])}, {long_date(source['as_of'])}</p></div>
<div class="bar big" aria-hidden="true">{bar}</div>
<details class="method"><summary>How status is assessed</summary>
<p>Progress labels are third-party classifications by <a href="{esc(source['url'])}">{esc(source['name'])}</a>, not findings by {esc(NAME)}. A status label is not proof of implementation: each Call needs evidence of action, evidence of outcomes, Indigenous-led perspectives and dated sources. Government announcements are not proof of completion.</p>
<p>The Government of Canada also publishes <a href="https://www.rcaanc-cirnac.gc.ca/eng/1524494530110/1557511412801">federal progress reporting</a>. It covers the 76 Calls involving federal leadership, while Indigenous Watchdog classifies all 94, so their percentages are not directly comparable.</p>
</details>
</section>
<section class="news-strip" aria-labelledby="ns-h">
<div class="ns-head"><h2 id="ns-h">Latest TRC News</h2><a href="/news/">All TRC news →</a></div>
<div class="ns-row">{strip}</div>
</section>
<section class="finder" aria-label="Find a Call">
<div class="finder-row">
<label class="search-box"><span class="sr">Search the Calls</span>{ICON_SEARCH}<input id="search" type="search" placeholder="Search 94 Calls" autocomplete="off"></label>
<label class="sr" for="topic">Topic</label>
<select id="topic"><option value="">All topics</option>{topic_opts}</select>
</div>
<div class="chips" role="group" aria-label="Filter by status">{status_btns}</div>
<p id="count" class="count" aria-live="polite">94 of 94 Calls to Action</p>
</section>
<section class="calls" id="calls">
{cards}
<p class="empty" id="empty" hidden>No Calls match that search. <button type="button" id="reset">Clear filters</button></p>
</section>'''
    ld = {"@context": "https://schema.org", "@type": "WebSite", "name": NAME, "url": SITE + "/"}
    return page(title="94 Calls to Action — status and progress tracker",
                description="Track all 94 Truth and Reconciliation Commission of Canada Calls to Action: plain-language summaries, responsible parties, independent progress status and related news.",
                path="/", active="calls", body=body, status_counts=counts,
                extra_head=f'<script type="application/ld+json">{json.dumps(ld)}</script>\n{AOS_HEAD}')


# ---------------------------------------------------------------- news
def call_tags(x):
    if x.get("calls"):
        return "".join(f'<a class="tag" href="/#call-{n}">Call #{n}</a>' for n in x["calls"])
    return f'<span class="tag">{esc(x.get("context") or "TRC context")}</span>'


def summary_of(x):
    t = x["sections"][0]["text"]
    if len(t) <= 260:
        return t
    cut = t[:260].rsplit(" ", 1)[0]
    return cut.rstrip(",;:") + "…"


def build_news_index(news, counts):
    if news:
        lead = news[0]
        lead_html = f'''<article class="news-lead">
<p class="meta"><time datetime="{lead['published']}">{long_date(lead['published'])}</time>{call_tags(lead)}</p>
<h2><a href="/news/{esc(lead['id'])}/">{esc(lead['headline'])}</a></h2>
<p>{esc(summary_of(lead))}</p>
<p><a class="more" href="/news/{esc(lead['id'])}/">Read the full update</a></p>
</article>'''
        cards = "".join(f'''<article class="news-card" data-calls="{' '.join(str(n) for n in x.get('calls', []))}">
<p class="meta"><time datetime="{x['published']}">{short_date(x['published'])}</time>{call_tags(x)}</p>
<h3><a href="/news/{esc(x['id'])}/">{esc(x['headline'])}</a></h3>
<p>{esc(summary_of(x))}</p>
</article>''' for x in news[1:])
    else:
        lead_html, cards = "<p>No updates have been published yet.</p>", ""
    body = f'''<section class="page-head">
<p class="eyebrow">Verified updates</p>
<h1>TRC News</h1>
<p class="lede">Dated, sourced developments linked to the Calls to Action they affect. New developments are published as separate stories; earlier reports stay part of the record.</p>
<p><a class="rss" href="/feed.xml">Follow by RSS</a></p>
</section>
<section class="news-list">
{lead_html}
<div class="news-grid">{cards}</div>
</section>
<section class="standards"><h2>Our standard</h2><p>Every story links to its sources, names the Calls it relates to, and separates announcements and funding from demonstrated implementation. A development is never presented as completing a Call unless the evidence shows it. Corrections are published as dated notes.</p></section>'''
    return page(title="TRC News — updates on the 94 Calls to Action",
                description="Verified, dated news about the Truth and Reconciliation Commission of Canada's 94 Calls to Action, each linked to its sources and the Calls it affects.",
                path="/news/", active="news", body=body, status_counts=counts)


def build_article(x, calls_by_n, counts, prev_next):
    secs = "".join(f'<section><h2>{esc(s["label"])}</h2><p>{esc(s["text"])}</p></section>' for s in x["sections"])
    srcs = "".join(f'<li><a href="{esc(s["url"])}" rel="noopener">{esc(s["title"])}</a></li>' for s in x["sources"])
    calls_box = ""
    if x.get("calls"):
        calls_box = '<aside class="art-calls"><h2>Calls to Action in this story</h2><ul>' + "".join(
            f'<li><a href="/#call-{n}"><b>#{n}</b> {esc(calls_by_n[n]["title"])}</a> <span class="pill {STATUS_CLASS[calls_by_n[n]["status"]]}">{esc(calls_by_n[n]["status"])}</span></li>' for n in x["calls"]) + "</ul></aside>"
    corr = "".join(f'<p class="correction"><b>Correction, {long_date(c["date"])}:</b> {esc(c["text"])}</p>' for c in x.get("corrections", []))
    pn = ""
    prev, nxt = prev_next
    if prev or nxt:
        pn = '<nav class="art-pn" aria-label="More stories">' + (f'<a href="/news/{esc(nxt["id"])}/">← Newer: {esc(nxt["headline"])}</a>' if nxt else "<span></span>") + (f'<a href="/news/{esc(prev["id"])}/">Older: {esc(prev["headline"])} →</a>' if prev else "") + "</nav>"
    review = f'<p class="review muted">How this story was prepared: {esc(x["review"]["method"])}.</p>' if x.get("review") else ""
    event = f'<span>Event date {long_date(x["date"])}</span>' if x["date"] != x["published"] else ""
    body = f'''<article class="article">
<p class="crumb"><a href="/news/">← TRC News</a></p>
<p class="meta"><time datetime="{x['published']}">Published {long_date(x['published'])}</time>{event}</p>
<h1>{esc(x['headline'])}</h1>
<p class="tags">{call_tags(x)}</p>
{corr}
<div class="art-body">{secs}</div>
<section class="art-sources"><h2>Sources</h2><ul>{srcs}</ul></section>
{calls_box}
{review}
{pn}
</article>'''
    ld = {"@context": "https://schema.org", "@type": "NewsArticle", "headline": x["headline"][:110],
          "datePublished": x["published"], "dateModified": x.get("updated", x["published"]),
          "mainEntityOfPage": f"{SITE}/news/{x['id']}/", "image": [f"{SITE}/assets/brand/og-image.png"],
          "publisher": {"@type": "Organization", "name": NAME, "logo": {"@type": "ImageObject", "url": f"{SITE}/assets/brand/icon-512.png"}}}
    return page(title=x["headline"], description=summary_of(x), path=f"/news/{x['id']}/", active="news",
                body=body, status_counts=counts, og_type="article",
                extra_head=f'<meta property="article:published_time" content="{x["published"]}">\n<script type="application/ld+json">{json.dumps(ld)}</script>')


def build_404(counts):
    body = '''<section class="page-head"><p class="eyebrow">Page not found</p><h1>That page isn't here</h1>
<p class="lede">It may have moved. Try the directory of all 94 Calls to Action or the latest TRC News.</p>
<p><a class="btn" href="/">94 Calls to Action</a> <a class="btn ghost" href="/news/">TRC News</a></p></section>'''
    return page(title="Page not found", description="Page not found.", path="/404.html", active="", body=body, status_counts=counts)


def rfc822(iso):
    d = datetime.datetime.combine(datetime.date.fromisoformat(iso), datetime.time(12, 0), tzinfo=datetime.timezone.utc)
    return d.strftime("%a, %d %b %Y %H:%M:%S +0000")


def build_feed(news):
    items = "".join(f'''<item><title>{esc(x['headline'])}</title><link>{SITE}/news/{x['id']}/</link><guid isPermaLink="true">{SITE}/news/{x['id']}/</guid><pubDate>{rfc822(x['published'])}</pubDate><description>{esc(summary_of(x))}</description></item>''' for x in news[:50])
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>{esc(NAME)} — TRC News</title><link>{SITE}/news/</link><description>Verified news about the 94 Calls to Action.</description><language>en-ca</language>{items}</channel></rss>
'''


def build_sitemap(news):
    today = datetime.date.today().isoformat()
    newest = news[0]["published"] if news else today
    urls = [(SITE + "/", newest), (SITE + "/news/", newest)] + [(f"{SITE}/news/{x['id']}/", x.get("updated", x["published"])) for x in news]
    body = "".join(f"<url><loc>{esc(u)}</loc><lastmod>{d}</lastmod></url>" for u, d in urls)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{body}</urlset>\n'


def redirect_page(target):
    t = esc(target)
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Moved</title>
<meta name="robots" content="noindex"><link rel="canonical" href="{SITE}{t}">
<meta http-equiv="refresh" content="0; url={t}"></head>
<body><p>This page has moved to <a href="{t}">{t}</a>.</p></body></html>
'''


def write(rel, text):
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists() or p.read_text(encoding="utf-8") != text:
        p.write_text(text, encoding="utf-8")
        print("wrote", rel)


def main():
    check_only = "--check" in sys.argv
    calls_data = load_calls()
    news = load_news()
    for x in news:
        if x["published"] > datetime.date.today().isoformat():
            raise ValueError(f"{x['id']}: published date is in the future")
    counts = {s: sum(1 for c in calls_data["calls"] if c["status"] == s) for s in STATUS_ORDER}
    print(f"{len(calls_data['calls'])} Calls, {len(news)} news stories, header style {HEADER}")
    if check_only:
        return
    calls_by_n = {c["n"]: c for c in calls_data["calls"]}
    write("index.html", build_calls(calls_data, news, counts))
    write("news/index.html", build_news_index(news, counts))
    keep = set()
    for i, x in enumerate(news):
        prev = news[i + 1] if i + 1 < len(news) else None
        nxt = news[i - 1] if i > 0 else None
        write(f"news/{x['id']}/index.html", build_article(x, calls_by_n, counts, (prev, nxt)))
        keep.add(x["id"])
    for d in (ROOT / "news").iterdir():
        if d.is_dir() and d.name not in keep:
            shutil.rmtree(d)
            print("removed news/" + d.name)
    write("404.html", build_404(counts))
    # Older addresses (/scripts/...) forward to the matching Call so existing links keep working.
    write("scripts/index.html", redirect_page("/"))
    for n in range(1, 95):
        write(f"scripts/revised-{n:02d}.html", redirect_page(f"/#call-{n}"))
    write("feed.xml", build_feed(news))
    write("sitemap.xml", build_sitemap(news))


if __name__ == "__main__":
    main()
