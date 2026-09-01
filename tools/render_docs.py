"""Render the how-to guides in docs-src/ into the site.

Deliberately a small, dependency-free markdown subset: headings, paragraphs, fenced code,
lists, blockquotes, tables, and inline code/bold/links. The guides are prose and code, so a
full CommonMark implementation would be weight for nothing, and the generator has to run in
CI with the standard library only.

Front matter is a simple key: value block between --- fences.
"""
import html
import os
import re

DOCS_SRC = "docs-src"
UPDATES_SRC = "updates"
ORDER = ["pc", "mobile-server", "mobile-companion", "csharp", "cpp"]


def parse_front_matter(text):
    """Split `---` front matter from the body.

    The BOM strip is not cosmetic. An editor that saves UTF-8 with a signature puts \ufeff
    before the opening `---`, the startswith test then fails, and EVERY key is silently lost:
    the page keeps building, but with its filename as the title and no summary. That shipped
    once, turning the "PC Launcher" and "Mobile Server" cards into "pc" and "mobile-server"
    with blank descriptions, and nothing failed to warn about it.
    """
    text = text.lstrip("\ufeff")
    meta, body = {}, text
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            for line in text[3:end].strip().splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip()] = v.strip()
            body = text[end + 4:].lstrip("\n")
    return meta, body


def inline(s):
    """Inline markdown on ALREADY-ESCAPED text."""
    s = re.sub(r"`([^`]+)`", lambda m: "<code>" + m.group(1) + "</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
    return s


def render(md):
    out, lines, i = [], md.split("\n"), 0
    while i < len(lines):
        line = lines[i]

        # Fenced code. Escaped, never inline-processed, so a * in code stays a *.
        m = re.match(r"^```(\w*)\s*$", line)
        if m:
            lang, i = m.group(1) or "text", i + 1
            buf = []
            while i < len(lines) and not lines[i].startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            out.append('<pre class="code" data-lang="%s"><code>%s</code></pre>'
                       % (html.escape(lang), html.escape("\n".join(buf))))
            continue

        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            lvl = len(m.group(1))
            txt = inline(html.escape(m.group(2).strip()))
            slug = re.sub(r"[^a-z0-9]+", "-", m.group(2).lower()).strip("-")
            out.append('<h%d id="%s">%s</h%d>' % (lvl, slug, txt, lvl))
            i += 1
            continue

        if re.match(r"^\s*>\s?", line):
            buf = []
            while i < len(lines) and re.match(r"^\s*>\s?", lines[i]):
                buf.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            out.append("<blockquote>%s</blockquote>" % inline(html.escape(" ".join(buf).strip())))
            continue

        if re.match(r"^\s*([-*]|\d+\.)\s+", line):
            ordered = bool(re.match(r"^\s*\d+\.\s+", line))
            items = []
            while i < len(lines) and re.match(r"^\s*([-*]|\d+\.)\s+", lines[i]):
                items.append(re.sub(r"^\s*([-*]|\d+\.)\s+", "", lines[i]))
                i += 1
            tag = "ol" if ordered else "ul"
            out.append("<%s>%s</%s>" % (tag, "".join(
                "<li>%s</li>" % inline(html.escape(t)) for t in items), tag))
            continue

        if not line.strip():
            i += 1
            continue

        buf = []
        while i < len(lines) and lines[i].strip() and not re.match(
                r"^(#{1,6}\s|```|\s*>|\s*([-*]|\d+\.)\s)", lines[i]):
            buf.append(lines[i].strip())
            i += 1
        out.append("<p>%s</p>" % inline(html.escape(" ".join(buf))))
    return "\n".join(out)


def load_all(root):
    """Every guide, in presentation order, with its front matter and rendered body."""
    docs = []
    d = os.path.join(root, DOCS_SRC)
    if not os.path.isdir(d):
        return docs
    for key in ORDER:
        path = os.path.join(d, key + ".md")
        if not os.path.exists(path):
            continue
        meta, body = parse_front_matter(open(path, encoding="utf-8").read())
        if not meta.get("title") or not meta.get("summary"):
            # Front matter did not parse, or is incomplete. Say so loudly: the page still
            # builds and looks almost right, which is exactly why this needs an alarm.
            print("WARNING: docs-src/%s.md has no %s in its front matter; the card will be "
                  "wrong" % (key, "title" if not meta.get("title") else "summary"))
        docs.append({
            "key": key,
            "title": meta.get("title", key),
            "anchor": meta.get("anchor", "docs-" + key),
            "status": meta.get("status", "published"),
            "note": meta.get("note"),
            "summary": meta.get("summary"),
            "html": render(body),
            "words": len(body.split()),
        })
    return docs


def load_updates(root):
    """Every update post, newest first.

    Posts are plain markdown in updates/ with a `date:` front-matter key in YYYY-MM-DD form.
    The date is the sort key AND the identity, so it is required: a post without one would
    float to an arbitrary position and silently reorder the feed on the next build.
    """
    posts = []
    d = os.path.join(root, UPDATES_SRC)
    if not os.path.isdir(d):
        return posts
    for name in sorted(os.listdir(d)):
        if not name.endswith(".md"):
            continue
        meta, body = parse_front_matter(open(os.path.join(d, name), encoding="utf-8").read())
        date = (meta.get("date") or "").strip()
        if not date:
            print("SKIPPING updates/%s: no date in front matter" % name)
            continue
        body = re.sub(r"<!--.*?-->", "", body, flags=re.S)
        posts.append({
            "key": name[:-3],
            "title": meta.get("title", name[:-3]),
            "date": date,
            "summary": meta.get("summary"),
            "html": render(body),
        })
    # Newest first. Sorting on the ISO date string is correct and needs no date parsing.
    posts.sort(key=lambda p: p["date"], reverse=True)
    return posts


def load_page(root, name):
    """A standalone hand-written page, such as About. Returns None when absent."""
    path = os.path.join(root, "pages", name + ".md")
    if not os.path.exists(path):
        return None
    meta, body = parse_front_matter(open(path, encoding="utf-8").read())
    # HTML comments are scaffolding notes to the author and must never reach the site.
    body = re.sub(r"<!--.*?-->", "", body, flags=re.S)
    todos = body.count("TODO:")
    return {
        "title": meta.get("title", name.title()),
        "status": meta.get("status", "published"),
        "todos": todos,
        "html": render(body),
    }
