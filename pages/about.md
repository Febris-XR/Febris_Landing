---
title: About Febris
status: published
---

## About Febris

I founded Febris years ago on a simple premise, to simulate hands-on education as closely as
possible using the new wave of VR headsets.

It was meant to be co-developed with a large healthcare system. They started a merger and the
deal fell apart. That is when I applied to Project Healthcare in Nashville, and the original
XR based nursing education went through it.

At the time, people had to use file sharing software like Dropbox to move these files around.
So Febris ended up needing to tackle far more than the one thing it set out to do.
Distribution, launching simulations, and privacy all had to be built along the way, because
none of it existed in a usable form.

Version 1 had no standardized educational records. Nothing available defined what a record of a
simulation session should look like, so whatever Febris captured was its own.

## Version 2

During COVID the pilots and agreements in healthcare, where Febris was focused, fell apart, and
version 2 began.

Standardized educational records came with it. The xAPI standard had been published eight years
earlier and adoption across learning platforms was still thin, but it was the right foundation,
so it was adopted and built in, and the integration libraries had to be written to go with it.

After the release of the Oculus Quest 2 a new layer was needed, the mobile suite. That is
probably the piece I am proudest of. It genuinely operated in a unique way, using peer to peer
networking to reach headsets directly.

Around then I saw that other developers in the space, content developers especially, needed the
same infrastructure Febris had built for its own internal use, and I was able to provide it.

## Version 3

The platform ballooned into version 3. That included a CRM, an LMS, SSO, MDM, a marketplace,
the integration libraries, and absolute privacy for the companies running their own end user
deployments.

Then I had to shelve Febris for approximately two years. I thought I would be able to pick it
back up where I left off. I was wrong.

## Why the direction changed

With changes in the Android operating system, Android is being locked down. It is similar to
what Meta did with their headsets, though not quite as restrictive. That makes the mobile
suite's real strength, being able to provision headsets quickly, basically useless.

Instead of designing around another massive change that Febris cannot control, made by
manufacturers, I took a different path.

## Where it stands now

The end user deployments are open source. They were always free to run. Now the source is
public as well, under the AGPL, and it is linked from the front page of this site.

If a group wants to use an end user deployment, they can host it themselves and use most of
what Febris was meant to do all along, with their own content. A central marketplace may be
reopened in the future.
