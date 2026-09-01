---
title: Mobile Server
anchor: docs-mobile-server
summary: Registering the server, pairing headsets over Bluetooth, and adding or removing devices.
status: published
note: This guide is text-only. The screenshots were removed because the pairing screen has changed since they were taken. The steps below were rewritten against the current source, including the Pair stage the earlier version omitted, but have not been walked through on a device.
---

## Mobile Server Documentation

### Background

This is documentation on how to use the Febris Mobile Server. You get it from the downloads section of this site, or from the Software Repository page of the node you connect to, which links to the same place. It is not published yet, and the downloads section says so plainly until it is.

**Not every aspect of the Febris mobile server is currently online. This will change in future releases.**

**If you violate your hardware's EULA by installing the Febris Mobile Suite, Febris takes no responsibility.**

### Requirements

Needed Items:

1. Android based Tablet (Android 10 [API 29] is optimal and minimum required OS, a phone can work but its size can make operation a challenge.)
2. Android based headset
3. OTG cable and second USB cable (optional but sometimes required for headsets that have removed the normal installer)

If your Android device does not support the installation of software outside of their tightly controlled marketplace, you may not be able to install the Febris software and we apologize for the inconvenience but there is nothing we can do about that situation.

### Registering a device

Registration is what lets your node send modules to this device and collect training data back from it. It runs in one direction: **your node creates the credential, and you carry it to the device.** Nothing is read off the device first.

1. On your node's portal, open **Hardware** and create the device.
2. The node generates a credential and **displays it once**. Copy it before leaving the page. It is stored only as a fingerprint, so nobody can look it up later, not even an administrator. If it is lost, use **Regenerate** on the Hardware list to issue a new one; the old credential stops working immediately and the device will not connect again until the new value is entered on it.
3. On the mobile server, open the configuration page and enter the credential in **Hardware License**. It is long, so pasting beats typing.
4. Press **Update Settings**. The credential is kept in the device's secure storage and used from then on.

The order matters. The mobile server cannot reach your node until it has been given a credential, so create the device on the node first.

### Setting up your device

The mobile server authenticates to your node with its **hardware licence**, not with a username and password. The user sign-in fields on the configuration screen are optional and are not needed for mobile server operations, so leave them blank unless your deployment specifically asks for them.

If the Hardware License field is empty, this device has not been registered yet, and the mobile server will say so rather than attempting to sign in. That is the expected state on a fresh install.

The developer option is an opt-in that points this client at a different node, supplied through the FEBRIS_DEVELOPER_API_URL environment variable. It ships with no address configured and there is no Febris operated account behind it, so leaving it off is correct unless you have been given an address to use.

If you are not a developer then the proper URL needs to be set up. Your IT administrator will have set up a private URL for your Febris operations. The URL can vary from a prefix, path, or port. If you do not know what these are please ask your IT Administrator. If the category does not exist, leave the section blank.

Pressing update settings saves your new configuration.

### Adding a headset

Register one headset at a time. The flow has three stages: discover the device, pair with it,
then install the Companion onto it.

**1. Discover.** Open **Configuration**, then **Pair New Device**, then press **Scan**. The
server searches over Bluetooth for Companions nearby.

**2. Pair.** Press **Pair** to open the pairing list. It shows devices that are *connected but
not yet paired*: a Companion appears here as soon as it joins the WiFi Direct group, which
happens before any pairing exists, so seeing it listed does not mean it is paired.

Pairing then shows a **six digit code on both devices**. Confirm the codes match before
accepting. If the list is empty, no Companion has joined the group yet, so the problem is at
the headset rather than on this screen.

Once paired, the device is added to your device list.

**3. Install the Companion.** Two routes.

*Over Bluetooth:* press the upload button to the right of the device in the list and tell the
tablet to send the file. You then have to open the transferred `.apk` on the headset yourself
to install it.

*Over USB OTG:* put both devices in developer mode first. Connect the OTG cable from the
machine running the Mobile Server to the headset. Approve every trust prompt that appears.
**Push and Install** and **Install** then become available at the top of the pairing page.

Press **Push and Install** first. It uploads the Companion's apk variants and installs them.
If the push fails partway through, try **Install** on its own before repeating the push: the
file it needs is probably already on the headset, and pushing again is usually wasted time.

### Removing a headset

A headset can be removed by pressing the trashcan icon on the left side of the device on the list.

### Api connection issues

The R3 Certification lead to issues with some systems. Previously working applications stopped working in September of 2022. If you are facing it and cannot get a new certificate. There are a few easy steps you can take for a temporary workaround.

Settings > Security > Encryption & Credentials > Trusted Credentials > Digital Signature Trust Co. (toggle)