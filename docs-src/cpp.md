---
title: C++ SDK
anchor: docs-sdk-cpp
summary: Consuming the native SDK through its flat C ABI: installing it, the calling conventions, and a minimal session.
status: published
---

## C++ simulation SDK

The native twin of the C# SDK. Use it when your simulation or engine cannot host managed
code. At the same MAJOR.MINOR version the two SDKs emit **byte-identical** statement JSON,
verified on every release by a conformance harness that runs both and compares the wire
output, so a mixed estate stays consistent.

Supported today: Windows x64, built with MSVC v143, C++17.

### Installing it

The SDK is published two ways.

Through vcpkg, using the Febris registry. Add the registry to your `vcpkg-configuration.json`,
pointing at `https://github.com/TRget88/Febris_VcpkgRegistry`, then:

```bash
vcpkg install febris-simulation-sdk
```

Or take the release bundle directly from the
[Febris_SDK releases](https://github.com/TRget88/Febris_SDK/releases). It contains the DLL,
the import library and the public header. Every release also ships a `SHA256SUMS` file, and
verifying the download against it is worth the few seconds.

### The interface is a flat C ABI

`FebrisSimApi.h` is the **only** supported binary interface. The C++ classes behind it are
deliberately not exported, so there is no MSVC name mangling to lock you to one compiler or
CRT, and the surface is callable by P/Invoke from a C# host if you need that.

If you would rather compile the SDK sources directly into your own target, define
`FEBRISSIM_STATIC` before including the header and it stops importing.

### Four conventions worth knowing before you start

**Status codes.** Functions returning `int32_t` yield `FEBRISSIM_OK` (0) or a negative error.
The library never lets a C++ exception cross the boundary.

```cpp
#define FEBRISSIM_OK                 0
#define FEBRISSIM_E_INVALID_ARG     (-1)   /* null or malformed required argument */
#define FEBRISSIM_E_EXCEPTION       (-2)   /* an internal failure caught at the boundary */
#define FEBRISSIM_E_NOT_INITIALIZED (-3)   /* call FebrisSimInitialize first */
```

**String outputs use a two-call buffer protocol.** Any function taking `(char* buf, int32_t cap)`
returns the **required byte count including the NUL terminator**, or a negative error. Call it
with `(NULL, 0)` to size the buffer, then again to fill it. When `cap` is greater than zero it
writes up to `cap - 1` bytes and NUL-terminates. All text is UTF-8.

**It is single-threaded by design**, exactly like the C# SDK. There is no internal
synchronisation. Drive it from one thread.

**Void functions swallow their failures**, mirroring the C# methods they came from. Register a
logger with `FebrisSimSetLogger` if you want to see them, otherwise a failed update is silent.

### Sizing a string result

This pattern appears throughout the API, so it is worth writing once:

```cpp
#include "FebrisSimApi.h"
#include <string>
#include <vector>

bool GetReferenceUuid(std::string& out)
{
    int32_t needed = FebrisSimGetReferenceUuid(nullptr, 0);   // ask for the size
    if (needed < 0) { return false; }                          // negative is an error code

    std::vector<char> buf(static_cast<size_t>(needed));        // needed INCLUDES the NUL
    if (FebrisSimGetReferenceUuid(buf.data(), needed) < 0) { return false; }

    out.assign(buf.data());
    return true;
}
```

### A minimal session

Initialise once at startup with the launch data your host passed you, update the statement as
the session progresses, then end it.

```cpp
#include "FebrisSimApi.h"
#include <vector>

// 1. Check you are compiled against the ABI you expect. This changes only when an existing
//    function changes shape, which is a MAJOR event. New functions do not bump it.
if (FebrisSimAbiVersion() != FEBRISSIM_ABI_VERSION) { /* refuse to run */ }

// 2. Initialise. febrisData is the launch payload; on Windows it arrives on the command line.
//    ready receives 1 when the platform handler accepted and persisted the first statement.
int32_t ready = 0;
int32_t extrasNeeded = FebrisSimInitialize(febrisData, FebrisSimOs_WindowsPC, &ready, nullptr, 0);
std::vector<char> extras(extrasNeeded > 0 ? extrasNeeded : 1);
FebrisSimInitialize(febrisData, FebrisSimOs_WindowsPC, &ready, extras.data(), extrasNeeded);

// On Windows the extras object is the string "null": the handler writes to the file system
// instead. On Android it carries the intent extras you broadcast onward.

// 3. During the session, keep the duration current.
FebrisSimDurationUpdateMs(elapsedMilliseconds);

// 4. End it, reporting completion and pass state with a scaled score.
int32_t endReady = 0;
FebrisSimEndSimulationWith(/* completed */ 1, /* passed */ 1, scaledScore, durationMs,
                           &endReady, nullptr, 0);
```

### Where the statement goes

The SDK does not talk to a node or to any LRS. It authors the statement and hands it to the
platform handler.

On Windows the handler writes a `{uuid}.json` file into your Documents folder, under
`Febris\statements\statements`. Something else moves it from there to a node, which is the PC
Statement Manager's job. If you are embedding the SDK in your own host, that hand-off is yours
to arrange, and `FebrisSimSetBasePath` lets you redirect the whole tree somewhere you control.

On Android nothing is written to disk. The SDK returns the statement as intent extras and your
host broadcasts them to the Companion.

### Enum values are the C# values

Every enum in the header carries the integer values from the C# API verbatim, so the two SDKs
agree on the wire and you can cross-reference the C# documentation without a translation table.

```cpp
enum FebrisSimOs { WindowsPC = 0, Android = 1, iOSvariant = 2, WinMobile = 3 };
enum FebrisSimLogLevel { Debug = 0, Info = 1, Warn = 2, Error = 3 };
```

### Versioning

The ABI evolves **additively** within a MINOR version: new functions may appear, existing
signatures never change shape. `FEBRISSIM_ABI_VERSION` is bumped only when an existing function
changes meaning, which is a MAJOR event. Checking it at startup, as above, is cheap insurance.
