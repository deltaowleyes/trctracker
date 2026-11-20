# TRC News — editorial standard and story format

## What counts as a story

A story is a dated, verifiable development that bears on one or more of the 94 Calls to Action. For example: legislation introduced, passed or in force; a court or tribunal decision; a funding announcement; an appointment; an official report or audit; a records, commemoration or search development; or a public statement from an Indigenous government or organization about an implementation issue.

Not a story: opinion pieces, events that have not happened yet (unless the announcement itself is news), anniversaries without new facts, or anything that cannot be confirmed from a reliable source.

## Standards

1. **Primary sources first.** Prefer the government department, legislature, court, or the Indigenous government or organization that made the announcement. Reputable news outlets are acceptable when no primary source is published; name the outlet in the source title.
2. **Every claim must be supported by a linked source.** Use `https` links only.
3. **Never overstate implementation.** Announcements, proposed budgets, funding commitments and bills are not completed actions. Say so plainly. A story never says a Call is complete unless the evidence shows it.
4. **Attribute concerns and positions.** "The Chiefs of Ontario say…", not "the process failed".
5. **Respect sensitive subjects.** Stories involving residential schools, children, health, burial sites and sacred matters must be precise and respectful. Do not speculate.
6. **Link the right Calls.** Only list a Call in `calls` when the development directly concerns it. If the link is general context, use an empty list and explain in `context`.
7. **Don't rewrite history.** Once published, a story is not silently changed. Add a dated entry to `corrections`.
8. **No duplicates.** Check `data/news/` for the same development before adding one. A genuinely new development in an ongoing story gets a new story.
9. **Be honest about how the story was made.** Record it in `review.method`, for example "AI-assisted research and drafting; every claim checked against the linked sources" or "Written and fact-checked by the editor".

## File format

One file per story in `data/news/`, named `YYYY-MM-DD-<id>.json` (the publication date, then the id).

```json
{
  "id": "short-lowercase-hyphenated-slug",
  "date": "2026-11-19",
  "published": "2026-11-20",
  "calls": [45],
  "context": "Treaty relationships; TRC Call #45",
  "headline": "Plain, factual headline",
  "sections": [
    { "label": "News", "text": "What happened, who said it, and when." },
    { "label": "Context", "text": "How it relates to the Call(s), without overstating it." },
    { "label": "Accountability", "text": "What remains unknown or unfinished, and what to watch." }
  ],
  "sources": [
    { "title": "Organization — title of release (Month D, YYYY)", "url": "https://..." }
  ],
  "review": { "method": "How the story was researched and checked", "reviewed_at": "2026-11-20" },
  "corrections": [
    { "date": "2026-11-22", "text": "What was corrected." }
  ]
}
```

- `id`: lower-case letters, digits and hyphens. It becomes the URL `/news/<id>/` and must never change after publication.
- `date`: the date the event happened. `published`: the date the story went up.
- `calls`: Call numbers 1–94. Can be empty.
- `corrections` and `review` are optional. Add `"status": "draft"` to keep a story out of the build.
- Keep each section to one paragraph of about 60–110 words.

`python3 tools/build.py --check` validates every story without writing pages.
