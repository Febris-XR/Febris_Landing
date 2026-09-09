---
title: Mobile Companion
anchor: docs-mobile-companion
summary: The headset app: how it gets installed, what it records, and how records reach your node.
status: published
---

## Mobile Companion

The Companion runs on the headset. It receives statements from the simulation running beside
it, holds them on the device, and hands them to your Mobile Server over a direct peer link.
It is the last hop before a learning record leaves the headset.

You normally do not install it by hand. It arrives from the Mobile Server, and that is the main
thing to understand about this component. An `.apk` is published on the release page for the
cases where you need one, and the downloads section links to it, but reaching for it by hand is
not the route this component is designed around.

### How it gets onto a headset

The Mobile Server installs it. The sequence is:

1. Your node holds a copy of the Companion package in its software catalogue.
2. The Mobile Server asks the node whether a newer version exists, calling
   `api/CompanionApp/getlatestversion` with its device token.
3. If the node has one, the Server downloads it from `api/CompanionApp/download/{uuid}`.
4. The Server pushes and installs it onto the connected headset over USB.

Steps 2 and 3 are automatic once the Server is pointed at your node. Step 4 is not. It needs the
headset on a USB OTG cable in developer mode, with the trust prompts approved, and a press of
**Push and Install** on the Server's pairing page.

The consequence worth planning around: **the headset can only be updated if your node holds
the package.** A copy sitting on someone's laptop is no use, because the Server asks the node,
not a person. If the Companion is missing from your node's catalogue there is nothing for the
Server to fetch and headsets stay on whatever version they already have.

### What it does during a session

The simulation does not write statement files on Android the way it does on Windows. Instead
the SDK hands the statement to the host as intent extras, and the host broadcasts them. The
Companion listens for three actions:

```text
com.febris.STATEMENT_CREATE
com.febris.STATEMENT_UPDATE
com.febris.STATEMENT_ERROR
```

Create opens a record, update revises it as the session progresses, and error captures a
failure the simulation wants recorded rather than lost. The Companion stores what it receives
on the device until the Mobile Server collects it.

### How records leave the headset

Over the direct peer link to the Mobile Server, not over your network and not to your node
directly. The Companion never talks to a node. The Server relays what it collects onward,
which is why a headset can run a full session with no network of its own.

### Requirements

An Android headset, paired with a Mobile Server, with the Server configured against your node.
The Companion has no configuration of its own to fill in.

### If a headset is not receiving updates

Work backwards along the chain, because the failure is almost always upstream of the headset.
Check that your node's catalogue actually holds a Companion package. Then that the Mobile
Server is pointed at the right node URL and its device credential is accepted. Then that the
Server and headset are paired and the USB connection is live. Only after all three would the
problem be on the headset itself.
