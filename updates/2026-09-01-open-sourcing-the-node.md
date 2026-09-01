---
title: The end-user deployment is open source
date: 2026-09-01
summary: Why the direction changed, what is published today, and what is still local-only.
---

The end-user deployment, the piece Febris calls the node, is open source. It was always free to
run. Now the source is public too, and a group that wants one can host it themselves with their
own content. The reasoning is on the [about page](../about.html).

## What is actually published

The node itself, and both simulation SDKs. The C# SDK is on nuget.org, the C++ SDK ships as a
release zip and through a vcpkg registry, and the two produce byte-identical output at the same
version so a mixed estate stays consistent.

## What is not published yet

The Windows client suite and the Android pair. The node's distribution surface works and this
site reads directly from the same feed the node does, so the moment those clients are published
the download cards here fill in on their own. Until then the cards say plainly that they are not
published rather than hiding the row.

## Honest caveats

This is pre-1.0 and there is one maintainer, so expect slow review and no on-call. Interfaces
can still change before 1.0, including configuration keys and API routes, and there is no
long-term-support branch. Upgrades run migrations at startup with no downgrade path yet, so take
a database backup first. The test suites are green and ship in the repository, which makes them
the honest measure of what is actually pinned rather than a claim you have to take on trust.
