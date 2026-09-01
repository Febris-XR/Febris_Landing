---
title: PC Launcher
anchor: docs-pc
summary: Registering a PC with your node, entering the credential it issues, and pointing the launcher at your node.
status: published
---

## PC Launcher Documentation

### Background

This is documentation on how to use the Febris PC Launcher. You get the PC package from the downloads section of this site, or from the Software Repository page of the node you connect to, which links to the same place. It is not published yet, and the downloads section says so plainly until it is.

**Not every aspect of the Febris PC Launcher is optimal. The PC software does not currently have a signing certificate. This will change in future releases.**

### Requirements

Needed Items:

1. VR ready PC running Windows 10 (Windows 11 may work but is untested)
2. Compatible headset and accompanying hardware

### Registering a device

Registration is what lets your node send modules to this PC and collect training data back from it. It runs in one direction: **your node creates the credential, and you carry it to the PC.** Nothing is read off the PC first.

1. On your node's portal, open **Hardware** and create the device.
2. The node generates a credential and **displays it once**. Copy it before leaving the page. It is stored only as a fingerprint, so nobody can look it up later, not even an administrator. If it is lost, use **Regenerate** on the Hardware list to issue a new one; the old credential stops working immediately and the device will not connect again until the new value is entered on it.
3. On the PC, open the launcher's configuration page and paste the credential into **Hardware License**.
4. Press **Save Settings**. The launcher keeps the credential encrypted on that machine and uses it from then on.

The order matters. The launcher cannot reach your node until it has been given a credential, so create the device on the node first.

### Setting up your device

The launcher authenticates to your node with its **hardware licence**, not with a username and password. The user sign-in fields on the configuration screen are optional and are not needed for launcher operations, so leave them blank unless your deployment specifically asks for them.

If the Hardware License field is empty, this PC has not been registered yet, and the launcher will say so rather than attempting to sign in. That is the expected state on a fresh install.

The developer option is an opt-in that points this client at a different node, supplied through the FEBRIS_DEVELOPER_API_URL environment variable. It ships with no address configured and there is no Febris operated account behind it, so leaving it off is correct unless you have been given an address to use.

If you are not a developer then the proper URL needs to be set up. Your IT administrator will have set up a private URL for your Febris operations. The URL can vary from a prefix, path, or port. If you do not know what these are please ask your IT Administrator. If the category does not exist, leave the section blank.
