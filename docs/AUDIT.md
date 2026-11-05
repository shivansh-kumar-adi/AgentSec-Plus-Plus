# AgentSec++ Baseline Audit

Audit date: 2026-11-05

## Scope and provenance

The supplied ZIP contained 29 files (42,032 bytes): 20 C++ headers, four C++
translation units, four Markdown documents, and one sample data file. The
original source is preserved under `security-engine/`; original documentation
is preserved as `docs/LEGACY_*`.

## Existing architecture and functionality

The baseline is a C++17 educational simulation. `EventFactory` parses a simple
CSV file into four polymorphic event types. `DecisionEngine` selects one of four
rules, calculates an in-memory Decision Confidence Score, and returns an action.
`SecurityAgent` prints and logs the result. Responses named `BlockIP` and
`QuarantineDevice` only print messages; no operating-system state is changed.

Verified on Windows with MSVC 19.44 (Visual Studio 2022 Build Tools): the main
program and test executable compile. All 6 existing assertion tests pass. The
MinGW `g++` found on PATH cannot start because of an `Illegal System DLL
Relocation`; the installed MSVC toolchain is the usable compiler.

There is no frontend, backend, HTTP/WebSocket API, database, authentication,
agent identity, AI provider, live telemetry collector, deployment manifest, CI,
or package/build configuration. The sample file is simulated input.

## Security and correctness findings

1. The JSON logger does not escape strings; quotes/control characters produce
   invalid JSON and permit log injection.
2. Severity, IP addresses, counters, paths, signatures, and reputation values
   are not validated or clamped.
3. CSV parsing does not support quoting and is unsuitable for untrusted input.
4. Raw owning pointers make ownership implicit and exception safety weak.
5. Timestamps use `ctime`, include a newline, use local time, and are not
   thread-safe.
6. Logs are not rotated, access-controlled, synchronized, or written atomically.
7. The notify decision band calls the rule's destructive-action factory; for
   some event types this returns Block/Quarantine, contrary to the threshold.
8. Action names imply enforcement but only print, which can mislead operators.
9. History and reputation are mutable in-memory state with no retention,
   expiry, concurrency control, or provenance.
10. Tests cover only six happy-path assertions and contain a semantic mismatch:
    "malware always quarantines" passes at DCS 0.705 even though the Balanced
    block threshold is 0.85, demonstrating finding 7.

No embedded credentials or shell-command execution were found in the baseline.

## Dependency and compatibility report

- Required by baseline: a C++17 compiler and standard library only.
- Verified compiler: MSVC from Visual Studio 2022 Build Tools.
- Broken compiler: `C:\MinGW\bin\g++.exe` on this host.
- CMake and Ninja were not installed at audit time.
- Python 3.10.11 and Node.js 22.23.2 are installed.
- Docker CLI is installed; daemon availability is verified separately.
- Platform behavior in the original code is portable, but it collects no real
  platform telemetry and performs no real response.

## Missing functionality

All requested product layers beyond the small simulation were absent: live
Windows/Linux collection, normalization, durable correlation, authenticated
ingestion, RBAC, incidents, investigations, approvals, auditable responses,
dashboard, migrations, streaming, containerization, CI, and deployment docs.

## Implementation roadmap

1. Preserve and harden the C++ decision core; add CMake and genuine, explicitly
   platform-scoped collectors with structured output.
2. Add an authenticated FastAPI service, durable schema/migrations, replay
   protection, RBAC, WebSockets, incidents, investigations, and approvals.
3. Add deterministic investigation fallback plus an optional constrained LLM
   provider whose output is schema-validated and never directly executed.
4. Add a React/TypeScript dashboard backed only by APIs and live events.
5. Add controlled response simulation first; gate real adapters behind explicit
   approval and least-privilege helpers.
6. Add unit/integration/end-to-end tests, Compose, CI, and deployment guidance.

