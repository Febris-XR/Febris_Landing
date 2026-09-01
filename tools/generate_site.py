#!/usr/bin/env python3
"""Generate the Febris landing site from the client-dist feed manifest.

The feed is the single source of truth. Every download card, version string, size and
checksum on the generated pages comes from manifest.json, so the site cannot drift from
what the feed actually serves. Nothing here is hand-maintained per release.

    python tools/generate_site.py            # fetch the live feed, write site/
    python tools/generate_site.py --check    # regenerate and fail if site/ is stale
    python tools/generate_site.py --manifest path.json   # build from a local copy

Standard library only, so CI needs no dependencies.
"""
import argparse
import html
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render_docs

FEED_URL = "https://raw.githubusercontent.com/Febris-XR/Febris_ClientDist/main/manifest.json"
# Must match the custom domain configured in Settings -> Pages, and must be a name that can
# legally hold a CNAME. The apex febr.is cannot: it carries the Google Workspace MX records,
# and RFC 1912 forbids a CNAME coexisting with any other record at the same name.
CUSTOM_DOMAIN = "www.febr.is"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")

# The five package kinds the feed schema defines, in the order a visitor should meet them.
# "acquire" is the honest answer to "how do I actually get this", which is not always a
# browser download: the Companion installs itself through the Mobile Server.
KINDS = [
    {
        "id": 100, "slug": "pc", "key": "PC", "name": "PC Client Suite",
        "blurb": "The Windows desktop suite: launcher, module manager, screen recorder, "
                 "statement manager and progress bar. Runs the simulation session on the "
                 "learner's machine and reports back to your node.",
        "acquire": "download",
        "platform": "Windows 10 or later, x64",
        "source": ("View the source", "https://github.com/Febris-XR/Febris_PC"),
    },
    {
        "id": 200, "slug": "mobile-server", "key": "AndroidMobileServer", "name": "Mobile Server",
        "blurb": "The Android MDM server. Pairs with headsets over WiFi Direct, distributes "
                 "module archives, and relays learning records back to your node.",
        "acquire": "download",
        "platform": "Android 10 or later, sideloaded",
        "source": ("View the source", "https://github.com/Febris-XR/Febris_MobileSuite"),
    },
    {
        "id": 300, "slug": "mobile-companion", "key": "AndroidMobileCompanion", "name": "Mobile Companion",
        "blurb": "The headset companion. Captures the session on-device and hands statements "
                 "to the Mobile Server over a direct peer link.",
        "acquire": "via-server",
        "platform": "Android 8 or later, installed onto the headset",
        "source": ("View the source", "https://github.com/Febris-XR/Febris_MobileSuite"),
    },
    {
        "id": 400, "slug": "sdk-csharp", "key": "CSharp", "name": "Simulation SDK for C#",
        "blurb": "Author conformant xAPI statements from a .NET simulation. Byte-identical "
                 "output to the C++ SDK at the same minor version.",
        "acquire": "package",
        "platform": ".NET Standard 2.0",
        "install": [("Add it to a project", "dotnet add package Febris.Simulation.XApiSdk --version {version}")],
        "home": ("View on nuget.org", "https://www.nuget.org/packages/Febris.Simulation.XApiSdk"),
        "source": ("View the source", "https://github.com/Febris-XR/Febris_SDK"),
    },
    {
        "id": 500, "slug": "sdk-cpp", "key": "CPP", "name": "Simulation SDK for C++",
        "blurb": "The native twin of the C# SDK, with a flat C ABI for engines and hosts that "
                 "cannot consume managed code. Verified byte-identical on every release.",
        "acquire": "package",
        "platform": "Windows x64, MSVC v143, C++17",
        "install": [
            ("Register the vcpkg registry", "vcpkg-configuration.json -> registries -> "
             "https://github.com/Febris-XR/Febris_VcpkgRegistry"),
            ("Then install", "vcpkg install febris-simulation-sdk"),
        ],
        "home": ("Browse the releases", "https://github.com/Febris-XR/Febris_SDK/releases"),
        "source": ("View the source", "https://github.com/Febris-XR/Febris_SDK"),
    },
]

CSS = """
:root {
  --ink: #14181c; --ink-soft: #4a545e; --ink-faint: #79848f;
  --ground: #fbfaf7; --panel: #ffffff; --line: #e3e0d9;
  --accent: #0f6d67; --accent-soft: #e6f1f0;
  --warn-bg: #fdf6e6; --warn-line: #e8d5a3; --warn-ink: #6b5310;
  --mono: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;
  --sans: system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --ink: #e8eaec; --ink-soft: #a3adb6; --ink-faint: #78838d;
    --ground: #14171a; --panel: #1b1f23; --line: #2c3238;
    --accent: #4fbfb4; --accent-soft: #16302e;
    --warn-bg: #2a2413; --warn-line: #5c4c1e; --warn-ink: #e3c877;
  }
}
:root[data-theme="dark"] {
  --ink: #e8eaec; --ink-soft: #a3adb6; --ink-faint: #78838d;
  --ground: #14171a; --panel: #1b1f23; --line: #2c3238;
  --accent: #4fbfb4; --accent-soft: #16302e;
  --warn-bg: #2a2413; --warn-line: #5c4c1e; --warn-ink: #e3c877;
}
* { box-sizing: border-box; }
body {
  margin: 0; background: var(--ground); color: var(--ink);
  font-family: var(--sans); font-size: 16px; line-height: 1.6;
  -webkit-font-smoothing: antialiased;
}
.wrap { max-width: 62rem; margin: 0 auto; padding: 0 1.5rem; }
header.top { border-bottom: 1px solid var(--line); padding: 1.1rem 0; }
header.top .wrap { display: flex; align-items: baseline; gap: 1.25rem; flex-wrap: wrap; }
.brand { font-weight: 650; letter-spacing: -0.01em; font-size: 1.05rem; color: var(--ink); text-decoration: none; }
.brand span { color: var(--accent); }
nav.top { margin-left: auto; display: flex; gap: 1.25rem; }
nav.top a { color: var(--ink-soft); text-decoration: none; font-size: 0.92rem; }
nav.top a:hover { color: var(--accent); }
.hero { padding: 4rem 0 3rem; border-bottom: 1px solid var(--line); }
.hero h1 { font-size: clamp(2rem, 5vw, 2.9rem); line-height: 1.15; margin: 0 0 1rem;
           letter-spacing: -0.025em; text-wrap: balance; }
.hero p.lede { font-size: 1.15rem; color: var(--ink-soft); max-width: 44rem; margin: 0 0 1.75rem; }
.cta { display: flex; gap: 0.75rem; flex-wrap: wrap; }
.btn { display: inline-block; padding: 0.6rem 1.15rem; border-radius: 6px; text-decoration: none;
       font-size: 0.95rem; font-weight: 550; border: 1px solid transparent; }
.btn-primary { background: var(--accent); color: #fff; }
.btn-primary:hover { filter: brightness(1.08); }
.btn-ghost { border-color: var(--line); color: var(--ink); }
.btn-ghost:hover { border-color: var(--accent); color: var(--accent); }
section { padding: 3.25rem 0; border-bottom: 1px solid var(--line); }
section h2 { font-size: 1.5rem; letter-spacing: -0.015em; margin: 0 0 0.5rem; }
section p.sub { color: var(--ink-soft); margin: 0 0 2rem; max-width: 46rem; }
.grid { display: grid; gap: 1.1rem; grid-template-columns: repeat(auto-fit, minmax(19rem, 1fr)); }
.card { scroll-margin-top: 1.5rem; background: var(--panel); border: 1px solid var(--line); border-radius: 9px;
        padding: 1.35rem; display: flex; flex-direction: column; }
.card h3 { margin: 0 0 0.15rem; font-size: 1.08rem; letter-spacing: -0.01em; }
.card .plat { font-size: 0.8rem; color: var(--ink-faint); margin: 0 0 0.7rem; }
.card p.desc { margin: 0 0 1.1rem; color: var(--ink-soft); font-size: 0.93rem; flex: 1; }
.pill { display: inline-block; font-size: 0.72rem; font-weight: 600; letter-spacing: 0.04em;
        text-transform: uppercase; padding: 0.16rem 0.5rem; border-radius: 999px; }
.pill-live { background: var(--accent-soft); color: var(--accent); }
.pill-soon { background: var(--line); color: var(--ink-faint); }
.meta { font-family: var(--mono); font-size: 0.78rem; color: var(--ink-faint);
        border-top: 1px solid var(--line); padding-top: 0.85rem; margin-top: 0.4rem; }
.meta div { display: flex; justify-content: space-between; gap: 1rem; padding: 0.12rem 0; }
.meta .hash { word-break: break-all; text-align: right; }
.note { background: var(--warn-bg); border: 1px solid var(--warn-line); color: var(--warn-ink);
        border-radius: 7px; padding: 0.8rem 1rem; font-size: 0.88rem; }
pre { background: var(--panel); border: 1px solid var(--line); border-radius: 7px;
      padding: 0.85rem 1rem; overflow-x: auto; font-family: var(--mono); font-size: 0.85rem;
      margin: 0.5rem 0 0; }
code { font-family: var(--mono); font-size: 0.88em; }
footer { padding: 2.5rem 0 3.5rem; color: var(--ink-faint); font-size: 0.88rem; }
footer a { color: var(--ink-soft); }
a { color: var(--accent); }
table.kinds { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
table.kinds th, table.kinds td { text-align: left; padding: 0.5rem 0.75rem 0.5rem 0;
                                  border-bottom: 1px solid var(--line); }
table.kinds th { color: var(--ink-faint); font-weight: 600; font-size: 0.78rem;
                 text-transform: uppercase; letter-spacing: 0.04em; }
.flow { display: grid; gap: 1.1rem; grid-template-columns: repeat(auto-fit, minmax(15rem, 1fr));
        counter-reset: step; }
.flow > div { position: relative; padding-top: 2.4rem; }
.flow > div::before {
  counter-increment: step; content: counter(step);
  position: absolute; top: 0; left: 0;
  width: 1.7rem; height: 1.7rem; border-radius: 50%;
  background: var(--accent-soft); color: var(--accent);
  font-family: var(--mono); font-size: 0.85rem; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
}
.flow h3 { margin: 0 0 0.35rem; font-size: 1rem; }
.flow p { margin: 0; color: var(--ink-soft); font-size: 0.92rem; }
.features { display: grid; gap: 0 2.5rem; grid-template-columns: repeat(auto-fit, minmax(20rem, 1fr)); }
.features dt { font-weight: 600; margin-top: 1.4rem; font-size: 0.97rem; }
.features dt:first-of-type { margin-top: 0; }
.features dd { margin: 0.2rem 0 0; color: var(--ink-soft); font-size: 0.92rem; }
.status { list-style: none; padding: 0; margin: 0; }
.status li { padding: 0.55rem 0 0.55rem 1.5rem; border-bottom: 1px solid var(--line);
             position: relative; color: var(--ink-soft); font-size: 0.93rem; }
.status li::before { content: ""; position: absolute; left: 0; top: 1.05rem;
                     width: 0.5rem; height: 0.5rem; border-radius: 50%; background: var(--accent); }
.status li:last-child { border-bottom: 0; }
.status strong { color: var(--ink); font-weight: 600; }
/* Brand mark. The logo is the original white one, which is white on transparency, so it
   needs a dark plate behind it or it disappears against the light theme's ground. The plate is
   a fixed colour on purpose rather than a theme token: it must stay dark in BOTH themes. */
.brand { display: inline-flex; align-items: center; text-decoration: none; }
.plate { display: inline-flex; align-items: center; justify-content: center;
  border-radius: 7px; padding: 0.3rem 0.55rem; }
.plate-dark { background: #0e1418; }
.plate-light { background: #ffffff; border: 1px solid var(--line); }
.brand img { height: 40px; width: auto; display: block; }

.flow-2 { grid-template-columns: repeat(auto-fit, minmax(20rem, 1fr)); margin-bottom: 2rem; }
p.tiny { font-size: 0.86rem; margin: 0.5rem 0 0; }

/* Logo page. Each variant is shown on the background it is designed for, so nobody picks the
   white one for a white page. */
.logogrid { display: grid; gap: 1.25rem; grid-template-columns: repeat(auto-fit, minmax(18rem, 1fr)); }
.logotile { border: 1px solid var(--line); border-radius: 10px; overflow: hidden; background: var(--panel); }
.logotile .plate { width: 100%; border-radius: 0; padding: 2rem; }
.logotile img { max-width: 100%; height: auto; display: block; }
.logotile .meta { padding: 0.9rem 1rem; border-top: 1px solid var(--line); }
.logotile .meta h3 { margin: 0 0 0.35rem; font-size: 0.98rem; }
.logotile .meta p { margin: 0 0 0.5rem; font-size: 0.86rem; color: var(--ink-soft); }
.logotile .meta code { font-size: 0.78rem; word-break: break-all; }

.postmeta { color: var(--ink-faint); font-size: 0.86rem; margin: 0 0 0.3rem; }

.doclist { display: grid; gap: 0.9rem; grid-template-columns: repeat(auto-fit, minmax(17rem, 1fr)); }
.doccard { display: block; background: var(--panel); border: 1px solid var(--line); border-radius: 8px;
           padding: 1.1rem; text-decoration: none; color: inherit; }
.doccard:hover { border-color: var(--accent); }
.doccard h3 { margin: 0 0 0.3rem; font-size: 1rem; color: var(--ink); }
.doccard p { margin: 0; font-size: 0.88rem; color: var(--ink-soft); }
.doccard .stub { color: var(--ink-faint); font-style: italic; }
article.doc { padding: 2.5rem 0 3rem; }
article.doc h2 { font-size: 1.7rem; margin: 0 0 1.2rem; letter-spacing: -0.02em; }
article.doc h3 { font-size: 1.15rem; margin: 2rem 0 0.6rem; }
article.doc h4 { font-size: 1rem; margin: 1.5rem 0 0.5rem; }
article.doc p { margin: 0 0 1rem; }
article.doc li { margin: 0.25rem 0; }
article.doc blockquote { margin: 1rem 0; padding: 0.7rem 1rem; border-left: 3px solid var(--accent);
                         background: var(--accent-soft); color: var(--ink-soft); font-size: 0.93rem; }
pre.code { background: var(--panel); border: 1px solid var(--line); border-radius: 7px;
           padding: 0.9rem 1.1rem; overflow-x: auto; font-family: var(--mono);
           font-size: 0.82rem; line-height: 1.5; margin: 0 0 1.1rem; }
.backlink { display: inline-block; margin-bottom: 1.5rem; font-size: 0.9rem; }
"""


def esc(s):
    return html.escape(str(s), quote=True)


def human_bytes(n):
    n = float(n)
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return ("%.0f %s" if unit == "B" else "%.1f %s") % (n, unit)
        n /= 1024


def page(title, body, depth=0):
    up = "../" * depth
    return """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s</title>
<meta name="description" content="Febris is an open source training and simulation platform. Self-host a delivery node and connect PC, mobile and XR clients.">
<link rel="icon" href="%sfavicon.ico" sizes="any">
<style>%s</style>
</head>
<body>
<header class="top"><div class="wrap">
  <a class="brand" href="%sindex.html">
    <span class="plate plate-dark"><img src="%smedia/images/Logos/FebrisLogo_White.png" alt="Febris"></span>
  </a>
  <nav class="top">
    <a href="%sindex.html#downloads">Downloads</a>
    <a href="%sindex.html#docs">Docs</a>
    <a href="%supdates.html">Updates</a>
    <a href="%sabout.html">About</a>
    <a href="%sindex.html#run">Self-host</a>
    <a href="https://github.com/Febris-XR/Febris_Node">Source</a>
  </nav>
</div></header>
%s
<footer><div class="wrap">
  <p>Febris is open source. The delivery node is AGPL-3.0, the SDKs are Apache-2.0, this site is MIT.</p>
  <p>
    <a href="https://github.com/Febris-XR/Febris_Node">Node</a> &middot;
    <a href="https://github.com/Febris-XR/Febris_PC">PC suite</a> &middot;
    <a href="https://github.com/Febris-XR/Febris_MobileSuite">Mobile suite</a> &middot;
    <a href="https://github.com/Febris-XR/Febris_SDK">SDK</a> &middot;
    <a href="https://github.com/Febris-XR/Febris_ClientDist">Distribution feed</a> &middot;
    <a href="https://github.com/Febris-XR/Febris_Landing">This site</a>
  </p>
</div></footer>
</body>
</html>
""" % (esc(title), up, CSS, up, up, up, up, up, up, up, body)


def card_for(kind, entry):
    """One download card. `entry` is the manifest row for this kind, or None."""
    head = '<h3>%s</h3><p class="plat">%s</p>' % (esc(kind["name"]), esc(kind["platform"]))
    desc = '<p class="desc">%s</p>' % esc(kind["blurb"])

    # The Companion is never a browser download, published or not, so say so in both states.
    # Otherwise the only card whose delivery differs looks identical to the ones that do not.
    via_server = ('<p class="note">Not a browser download. The Companion is delivered to the '
                  'headset by your Mobile Server over a direct link, so it installs itself once '
                  'the Server is paired and pointed at your node.</p>')

    # The source link renders whether or not a signed BINARY exists. Every component here is
    # public already, so a card that says "not yet published" and then offers no route at all
    # reads as though the whole thing is missing, when only the signed artifact is.
    src = ""
    if kind.get("source"):
        slabel, shref = kind["source"]
        src = '<div class="cta"><a class="btn btn-ghost" href="%s">%s</a></div>' % (
            esc(shref), esc(slabel))

    if entry is None:
        pill = '<span class="pill pill-soon">Source only</span>'
        if kind["acquire"] == "via-server":
            action = via_server
        else:
            action = ('<p class="note">The source is public and builds today. What is missing is a '
                      'signed binary, which is what release signing gates, and one appears here '
                      'automatically once the feed carries it.</p>')
        return '<div class="card" id="%s">%s %s %s %s %s</div>' % (
            kind["slug"], pill, head, desc, action, src)

    art = entry["artifact"]
    version = entry.get("version", "")
    pill = '<span class="pill pill-live">Version %s</span>' % esc(version)

    if kind["acquire"] == "via-server":
        action = via_server
    else:
        bits = ['<a class="btn btn-primary" href="%s">Download</a>' % esc(art["url"])]
        if kind.get("home"):
            label, href = kind["home"]
            bits.append('<a class="btn btn-ghost" href="%s">%s</a>' % (esc(href), esc(label)))
        if kind.get("source"):
            slabel, shref = kind["source"]
            bits.append('<a class="btn btn-ghost" href="%s">%s</a>' % (esc(shref), esc(slabel)))
        action = '<div class="cta">%s</div>' % "".join(bits)
        for label, cmd in kind.get("install", []):
            action += "<p class=\"plat\" style=\"margin:0.9rem 0 0\">%s</p><pre>%s</pre>" % (
                esc(label), esc(cmd.replace("{version}", version)))

    meta = ('<div class="meta">'
            '<div><span>File</span><span class="hash">%s</span></div>'
            '<div><span>Size</span><span>%s</span></div>'
            '<div><span>SHA-256</span><span class="hash">%s</span></div>'
            '</div>') % (esc(art["fileName"]), esc(human_bytes(art["sizeBytes"])), esc(art["sha256"]))

    return '<div class="card" id="%s">%s %s %s %s %s</div>' % (kind["slug"], pill, head, desc, action, meta)


def build_doc(doc):
    """One guide as its own page."""
    note = ('<blockquote>%s</blockquote>' % esc(doc["note"])) if doc.get("note") else ""
    body = """
<article class="doc"><div class="wrap">
  <a class="backlink" href="../index.html#docs">Back to all guides</a>
  %s
  %s
</div></article>
""" % (note, doc["html"])
    return page("%s, Febris documentation" % doc["title"], body, depth=1)


def build_about(about):
    """The hand-written About page. Carries a visible draft banner while unwritten, so a
    half-finished story cannot be published by accident."""
    banner = ""
    if about["todos"]:
        banner = ('<blockquote><strong>Draft.</strong> This page still has %d unwritten '
                  'section(s) and is not ready to publish.</blockquote>' % about["todos"])
    body = """
<article class="doc"><div class="wrap">
  %s
  %s
</div></article>
""" % (banner, about["html"])
    return page("About Febris", body)


def build_logo():
    """Brand assets, deliberately UNLISTED: reachable by URL, absent from every nav.

    It exists so the maintainer has one page to point a designer or a press contact at.

    The asset paths are NOT arbitrary. `/media/images/Logos/FebrisLogo_White.png` is the exact
    path the old marketing site served, and five shipped email templates across the Admin
    Portal, SSO and Marketing API hardcode `https://febr.is/media/images/Logos/FebrisLogo_White.png`
    as the header image. Every one of those mails already in somebody's inbox fetches that URL
    when it is opened. Serving the file from the same path is what keeps them from breaking, so
    these two paths must not be "tidied" into an assets folder.
    """
    body = """
<article class="doc"><div class="wrap">
  <h1>Brand assets</h1>
  <p>The Febris mark in its two original variants. Right-click to save, or hotlink directly.
  These URLs are stable and are not going to move.</p>

  <div class="logogrid">
    <div class="logotile">
      <div class="plate plate-dark"><img src="media/images/Logos/FebrisLogo_White.png" alt="Febris logo, white"></div>
      <div class="meta">
        <h3>White</h3>
        <p>For dark backgrounds. This is the variant the email templates use.</p>
        <code>https://www.febr.is/media/images/Logos/FebrisLogo_White.png</code>
      </div>
    </div>
    <div class="logotile">
      <div class="plate plate-light"><img src="media/images/Logos/FebrisLogo_Blue.png" alt="Febris logo, blue"></div>
      <div class="meta">
        <h3>Blue</h3>
        <p>For light backgrounds.</p>
        <code>https://www.febr.is/media/images/Logos/FebrisLogo_Blue.png</code>
      </div>
    </div>
  </div>

  <h2>Why these paths look old</h2>
  <p>They are the paths the previous marketing site used. Emails sent from Febris over the years
  embed the white logo by absolute URL, and those messages still sit in people's inboxes and
  still fetch the image when opened. Keeping the path identical is what stops those older mails
  from rendering with a broken image, so the location is deliberate rather than untidy.</p>

  <h2>Favicon</h2>
  <p>The site icon is the original one as well: <code>https://www.febr.is/favicon.ico</code></p>

  <p class="tiny"><a href="index.html">Back to the site</a></p>
</div></article>
"""
    return page("Febris brand assets", body)


def build_updates(posts):
    """The updates index. Empty is a legitimate state and says so rather than rendering
    an empty list that looks broken."""
    if posts:
        items = "".join(
            '<a class="doccard" href="updates/%s.html"><p class="postmeta">%s</p>'
            '<h3>%s</h3>%s</a>' % (
                p["key"], esc(p["date"]), esc(p["title"]),
                '<p>%s</p>' % esc(p["summary"]) if p.get("summary") else "")
            for p in posts)
        listing = '<div class="doclist">%s</div>' % items
    else:
        listing = "<p>No updates posted yet.</p>"

    body = """
<article class="doc"><div class="wrap">
  <h1>Updates</h1>
  <p>Release notes and progress on the project. Written by hand, so silence here means nothing
  was worth saying rather than that something is broken.</p>
  %s
</div></article>
""" % listing
    return page("Febris updates", body)


def build_update(post):
    """One update post as its own page."""
    body = """
<article class="doc"><div class="wrap">
  <a class="backlink" href="../updates.html">Back to all updates</a>
  <p class="postmeta">%s</p>
  <h1>%s</h1>
  %s
</div></article>
""" % (esc(post["date"]), esc(post["title"]), post["html"])
    return page("%s, Febris updates" % post["title"], body, depth=1)


def build_index(manifest, docs):
    by_kind = {}
    for p in manifest.get("packages", []):
        if not p.get("obsolete"):
            by_kind.setdefault(p.get("kindId"), p)

    cards = "".join(card_for(k, by_kind.get(k["id"])) for k in KINDS)
    live = sum(1 for k in KINDS if by_kind.get(k["id"]))

    doccards = "".join(
        '<a class="doccard" id="%s" href="docs/%s.html"><h3>%s</h3>%s</a>' % (
            d["anchor"], d["key"], esc(d["title"]),
            ('<p class="stub">Not written yet</p>' if d["status"] == "stub"
             else '<p>%s</p>' % esc(d.get("summary") or "")))
        for d in docs)

    rows = "".join(
        '<tr><td>%s</td><td>%s</td><td>%s</td></tr>' % (
            esc(k["name"]), esc(k["platform"]),
            "Published" if by_kind.get(k["id"]) else "Source only")
        for k in KINDS)

    body = """
<div class="hero"><div class="wrap">
  <h1>XR and simulation training, on infrastructure you own.</h1>
  <p class="lede">Febris delivers training to headsets and desktops, and records what actually
  happened during the session as xAPI. One node owns everything it needs: identity and accounts,
  cohorts, curricula and modules, a statement store, usage analytics, and the artifact store that
  distributes the client software to devices. There is no Febris account, no licence key, and no
  service the maintainer operates.</p>
  <div class="cta">
    <a class="btn btn-primary" href="#downloads">Get the software</a>
    <a class="btn btn-ghost" href="#run">Run a node</a>
  </div>
</div></div>


<section id="how"><div class="wrap">
  <h2>How it fits together</h2>
  <p class="sub">Three pieces. A server you run, clients that deliver the training, and an SDK
  for the people building the simulations.</p>
  <div class="flow">
    <div>
      <h3>The node</h3>
      <p>An ASP.NET Core server you host. It holds your accounts and curricula, ingests xAPI
      statements from devices, and hands out the client software those devices run.</p>
    </div>
    <div>
      <h3>The clients</h3>
      <p>A Windows suite for desktop simulation, and an Android pair where a Mobile Server
      distributes modules to headsets over a direct WiFi link and relays their records back.</p>
    </div>
    <div>
      <h3>The SDK</h3>
      <p>Drop it into your own simulation to emit conformant statements. C# and C++ produce
      byte-identical output at the same version, so a mixed estate stays consistent.</p>
    </div>
  </div>
</div></section>

<section id="node"><div class="wrap">
  <h2>What a node gives you</h2>
  <p class="sub">All of this is code in the repository rather than a roadmap. Where something is
  a seam rather than a finished feature, the project says so in its own README.</p>
  <dl class="features">
    <dt>Learning records that survive audit</dt>
    <dd>A dedicated xAPI store with its own database, statements deduplicated on the identifier
    their producer assigned, and the raw submission preserved alongside the parsed form.</dd>

    <dt>Cohorts, curricula and modules</dt>
    <dd>Organise learners, group them, assign curricula, and version the module archives that
    devices pull down.</dd>

    <dt>Client distribution built in</dt>
    <dd>The node is the artifact store. Devices ask it for the current build and it serves the
    bytes, checksum recorded, so a headset updates without anyone visiting a website.</dd>

    <dt>Transport hardening the operator controls</dt>
    <dd>HSTS, an exact-match CORS allow-list, frame and content-type headers, all from one
    configuration section, with defaults chosen so a node behind a TLS proxy does not loop.</dd>

    <dt>Rate limiting that ships on by default</dt>
    <dd>Per-IP endpoint rules returning 429, tuned tightly on login, password reset and token
    endpoints, retunable without a rebuild.</dd>

    <dt>Nothing phones home</dt>
    <dd>Federation to a hub exists as an opt-in gate and defaults to off. Learning records have
    no upward path at all. An air-gapped site is a supported deployment, not an afterthought.</dd>
  </dl>
</div></section>

<section id="run"><div class="wrap">
  <h2>Run one</h2>
  <p class="sub">A Docker Compose stack: Postgres 16, Valkey 8, the API, the portal, and a Caddy
  reverse proxy that issues its own certificate for local use.</p>
  <pre>git clone https://github.com/Febris-XR/Febris_Node.git febris-node &amp;&amp; cd febris-node
./selfhost/generate-env.sh
docker compose up -d --build</pre>
  <p class="sub" style="margin-top:1.25rem">The generated environment file prints your first
  login. Everything else, including backups, upgrades, TLS and going to production, is in
  <a href="https://github.com/Febris-XR/Febris_Node/blob/main/SELF_HOSTING.md">SELF_HOSTING.md</a>.</p>
  <table class="kinds" style="margin-top:2rem">
    <thead><tr><th>Component</th><th>Platform</th><th>Status</th></tr></thead>
    <tbody>%(rows)s</tbody>
  </table>
</div></section>

<section id="docs"><div class="wrap">
  <h2>How to use it</h2>
  <p class="sub">Guides for each piece, carried over from the node's own documentation. Where a
  guide is unwritten or known to be incomplete, it says so on the page rather than pretending
  otherwise.</p>

  <div class="flow flow-2">
    <div>
      <h3>PC</h3>
      <p>The PC suite runs the simulation on a Windows machine. You install it once, register
      that PC on your node's Hardware page, and paste in the credential the node issues. From
      then on the Launcher pulls the modules the learner is assigned, starts the session, and the
      Statement Manager sends the resulting xAPI records back to your node on its own.</p>
      <p class="tiny"><a href="docs/pc.html">Read the PC guide</a></p>
    </div>
    <div>
      <h3>Mobile Server</h3>
      <p>The Mobile Server is the Android app that manages your headsets. You register it the
      same way, then use it to discover a headset over Bluetooth, pair with it by confirming a
      six digit code shown on both screens, and install the Mobile Companion onto it. From then
      on it distributes module archives over a direct WiFi link and relays the resulting records
      back to your node, so the headsets never need your network credentials.</p>
      <p class="tiny"><a href="docs/mobile-server.html">Read the Mobile Server guide</a></p>
    </div>
  </div>

  <div class="doclist">%(doccards)s</div>
</div></section>

<section id="downloads"><div class="wrap">
  <h2>Downloads</h2>
  <p class="sub">Every version, size and checksum below is read straight from the distribution
  feed, so this page describes exactly what the feed serves and nothing else. %(live)d of %(total)d components
  are published today, and the rest say so plainly rather than being hidden.</p>
  <div class="grid">%(cards)s</div>
</div></section>
""" % {"live": live, "total": len(KINDS), "cards": cards, "rows": rows, "doccards": doccards}
    return page("Febris, self-hosted XR and simulation training", body)


def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", help="build from a local manifest instead of fetching")
    ap.add_argument("--check", action="store_true", help="fail if the committed site is stale")
    args = ap.parse_args()

    if args.manifest:
        manifest = json.load(open(args.manifest, encoding="utf-8"))
    else:
        with urllib.request.urlopen(FEED_URL, timeout=30) as r:
            manifest = json.loads(r.read().decode("utf-8"))

    if manifest.get("schemaVersion") != 1:
        print("refusing: unknown feed schemaVersion %r" % manifest.get("schemaVersion"))
        return 1

    docs = render_docs.load_all(ROOT)
    pages = {os.path.join(SITE, "index.html"): build_index(manifest, docs)}
    for d in docs:
        pages[os.path.join(SITE, "docs", d["key"] + ".html")] = build_doc(d)

    # Unlisted by design; see build_logo.
    pages[os.path.join(SITE, "logo.html")] = build_logo()

    posts = render_docs.load_updates(ROOT)
    pages[os.path.join(SITE, "updates.html")] = build_updates(posts)
    for p in posts:
        pages[os.path.join(SITE, "updates", p["key"] + ".html")] = build_update(p)

    about = render_docs.load_page(ROOT, "about")
    if about:
        pages[os.path.join(SITE, "about.html")] = build_about(about)
        if about["todos"]:
            print("NOTE: pages/about.md still has %d unwritten TODO section(s); "
                  "about.html carries a draft banner" % about["todos"])
    # Pages needs this or it runs the output through Jekyll and drops anything underscored.
    pages[os.path.join(SITE, ".nojekyll")] = ""
    # The custom domain has to live INSIDE the artifact. Under Actions-based deployment the
    # uploaded directory IS the published site, so a CNAME sitting at the repository root is
    # never deployed and the custom domain can be dropped on the first run. Emitted here so
    # www.febr.is survives every deploy. Deleting this file gives the domain back to the
    # default trget88.github.io/Febris_Landing address, which is the intended way to opt out.
    pages[os.path.join(SITE, "CNAME")] = CUSTOM_DOMAIN + "\n"

    if args.check:
        stale = []
        for path, content in pages.items():
            existing = open(path, encoding="utf-8", newline="").read() if os.path.exists(path) else None
            if existing != content:
                stale.append(os.path.relpath(path, ROOT).replace(os.sep, "/"))
        if stale:
            print("STALE: %s" % ", ".join(stale))
            print("The feed has moved on. Run: python tools/generate_site.py")
            return 1
        print("site/ is current with the feed")
        return 0

    for path, content in pages.items():
        write(path, content)
        print("wrote %s" % os.path.relpath(path, ROOT).replace(os.sep, "/"))
    print("%d package(s) in the feed" % len(manifest.get("packages", [])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
