# TRC Tracker — trctracker.ca

A static website that tracks the Truth and Reconciliation Commission of Canada's 94 Calls to Action. It has two sections:

- **94 Calls to Action** (`/`): a searchable directory of all 94 Calls with plain-language summaries, responsible parties, an independent progress status, related Calls and related news.
- **TRC News** (`/news/`): dated, sourced news stories, each linked to the Calls it affects, with an RSS feed.

There is no database, server code or build framework. Everything is generated from JSON files by one Python script that uses only the standard library, and the result is plain HTML that any static host can serve.

## How it fits together

| Path | What it is |
|---|---|
| `site.config.json` | Site name, URL, header style (`A`, `B` or `C`) and asset version |
| `data/calls.json` | The 94 Calls and the progress status source and date |
| `data/news/*.json` | One file per news story |
| `tools/build.py` | Builds every page from the data |
| `tools/check_links.py` | Checks that every internal link resolves |
| `assets/` | `site.css`, `site.js` and the brand images in `assets/brand/` |
| `NEWS-GUIDE.md` | Editorial standard and the format for news stories |
| `.github/workflows/build.yml` | Rebuilds the site on GitHub whenever data or tools change |

Generated files (do not edit by hand): `index.html`, `news/`, `404.html`, `feed.xml`, `sitemap.xml`.

## Common tasks

**Build locally**

```sh
python3 tools/build.py
python3 tools/check_links.py
python3 -m http.server 8000   # then open http://localhost:8000
```

**Add a news story.** Add a JSON file to `data/news/` in the format described in `NEWS-GUIDE.md`, then build (or push and let the workflow build it).

**Update progress statuses.** Edit `status` for each Call in `data/calls.json` and update `status_source.as_of`. The header and status panel recount themselves. If you change the date, also update the "Indigenous Watchdog, Oct 1, 2026" label in `tools/build.py` (header style C).

**Change the header style.** Set `header_style` in `site.config.json` to `A` (classic masthead), `B` (red band with badge) or `C` (progress strip) and rebuild.

**Bust browser caches after changing CSS or JS.** Increase `asset_version` in `site.config.json`.

## Hosting

The site is set up for GitHub Pages (`CNAME` holds the custom domain, and `.nojekyll` is present). It also works unchanged on Netlify, Cloudflare Pages or any web server: publish the repository root.

For GitHub Pages: Settings → Pages → Source "Deploy from a branch", branch `main`, folder `/ (root)`, custom domain as in `CNAME`, then tick "Enforce HTTPS" once the certificate is issued. DNS for an apex domain points four `A` records at 185.199.108.153, 185.199.109.153, 185.199.110.153 and 185.199.111.153, plus a `www` CNAME to `<github-user>.github.io`.

## Sources and attribution

- Original Calls to Action: [National Centre for Truth and Reconciliation](https://nctr.ca/about/truth-and-reconciliation-commission-of-canada-calls-to-action/). Summaries on the site are plain-language, not the TRC's original wording.
- Progress statuses: third-party classifications by [Indigenous Watchdog](https://www.indigenouswatchdog.org/), credited on every page.
- Federal reporting: [Crown-Indigenous Relations and Northern Affairs Canada](https://www.rcaanc-cirnac.gc.ca/eng/1524494530110/1557511412801).

No analytics, cookies or tracking are included. If you add analytics, add a privacy notice too.
