# Febris_Landing

The public front door for [Febris](https://github.com/Febris-XR/Febris_Node), an open source
training and simulation platform. This repository builds the site that tells people what Febris
is and hands them the client software and SDKs.

## How it works

The site is **generated from the distribution feed**, not hand written. `tools/generate_site.py`
reads `manifest.json` from
[Febris_ClientDist](https://github.com/Febris-XR/Febris_ClientDist) and renders `site/`. Every
version string, file size, checksum and download link on the page comes from that manifest, so
the page cannot claim something the feed does not actually serve.

```
Febris_ClientDist/manifest.json  ->  tools/generate_site.py  ->  site/  ->  GitHub Pages
docs-src/*.md  pages/about.md  updates/*.md  ->  tools/render_docs.py  ->  site/
```

Only the download data comes from the feed. The prose pages are hand written markdown rendered
by `tools/render_docs.py`, which implements the small subset of markdown this site needs and
has no third-party dependency.

`site/` is committed rather than built only inside a runner, so what is deployed is reviewable
in the diff. The workflow enforces that: a pull request fails if the committed site no longer
matches the live feed, and on `main` the scheduled run regenerates and commits any drift itself.
This mirrors how `docs/STATUS.md` is handled in the node repository.

## Working on it

```bash
python tools/generate_site.py            # fetch the live feed and rebuild site/
python tools/generate_site.py --check    # fail if site/ is stale, what CI runs
python tools/generate_site.py --manifest local.json   # build from a local manifest
```

Standard library only. No build toolchain, no dependencies, no package manager.

Open `site/index.html` in a browser to review changes before committing.

## Hand written content

| Source | Becomes | Notes |
|---|---|---|
| `docs-src/*.md` | `site/docs/*.html` | One how-to guide per client or SDK |
| `pages/about.md` | `site/about.html` | Carries a visible draft banner while any `TODO:` remains |
| `updates/*.md` | `site/updates.html` and `site/updates/*.html` | Newest first |

### Front matter is load-bearing, and fails quietly

Each file opens with a `---` block. `docs-src` entries need `title`, `anchor`, `summary` and
`status`; `updates` entries need `title`, `date` (YYYY-MM-DD, used as the sort key) and
`summary`.

**Save these files as UTF-8 WITHOUT a byte order mark.** A BOM sits before the opening `---`,
the parser's `startswith` test fails, and every key is silently dropped: the page still builds,
but with the filename as its title and no description. That shipped once, turning the "PC
Launcher" and "Mobile Server" cards into "pc" and "mobile-server". The parser now strips a BOM
defensively and the build prints a warning for any guide missing a title or summary, but the
underlying trap is worth knowing about.

### Posting an update

Drop a file in `updates/`, named however you like, then rebuild:

```
---
title: What happened
date: 2026-09-01
summary: One line, shown on the updates index.
---

Body in markdown.
```

## Brand assets, and why their paths look odd

`site/favicon.ico` and `site/media/images/Logos/` come from the previous Febris marketing site
and **are served from the exact paths that site used**. That is deliberate and must not be
"tidied" into an assets folder.

Five shipped email templates, across the Admin Portal, SSO and the Marketing API, hardcode
`https://febr.is/media/images/Logos/FebrisLogo_White.png` as their header image. Every one of
those messages already sitting in somebody's inbox fetches that URL when it is opened. Moving
the file breaks them all, retroactively and permanently.

`site/logo.html` presents both logo variants with their stable URLs. It is **unlisted on
purpose**: reachable by URL, absent from every navigation menu, so it can be handed to a
designer or a press contact without becoming part of the site's structure.

The white logo is white on transparency, so it is always rendered on a dark plate. That plate
keeps a fixed dark colour in both light and dark themes, because a theme-following background
would make the mark disappear on the light one.

## What the page shows

One card per package kind the feed schema defines: the PC client suite, the Mobile Server, the
Mobile Companion, and the two simulation SDKs. Kinds the feed does not yet carry render an
honest "not yet published" state rather than being hidden, so the page never implies the
catalogue is complete when it is not.

The Mobile Companion is a deliberate exception. It is never a browser download, because it is
delivered to the headset by the Mobile Server over a direct peer link, and the card says so in
every state.

## Publishing

GitHub Pages must be enabled with **Source: GitHub Actions** for the deploy step to work. After
that, pushes to `main`, the daily schedule, and a `repository_dispatch` of type `feed-updated`
from the distribution repository all republish the site.

The site is MIT licensed. The software it points at is not: the delivery node is AGPL-3.0 and
the SDKs are Apache-2.0.
