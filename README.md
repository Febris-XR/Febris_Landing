# Febris_Landing

The public front door for [Febris](https://github.com/TRget88/Febris_Node), an open source
training and simulation platform. This repository builds the site that tells people what Febris
is and hands them the client software and SDKs.

## How it works

The site is **generated from the distribution feed**, not hand written. `tools/generate_site.py`
reads `manifest.json` from
[Febris_ClientDist](https://github.com/TRget88/Febris_ClientDist) and renders `site/`. Every
version string, file size, checksum and download link on the page comes from that manifest, so
the page cannot claim something the feed does not actually serve.

```
Febris_ClientDist/manifest.json  ->  tools/generate_site.py  ->  site/  ->  GitHub Pages
```

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
