# AgentSec++

**An Object-Oriented, Explainable Security Agent Framework for Autonomous Cyber Defense**

AgentSec++ is a C++17 mini-project that simulates a rule-based autonomous
security agent. It observes security events, evaluates them against a set
of rules, computes a transparent confidence score for its decision, and
executes an appropriate response — while explaining *why* it made that
choice at every step.

The project is built to demonstrate core Object-Oriented Programming
concepts (inheritance, polymorphism, encapsulation, composition) alongside
two classic software design patterns (Factory and Strategy), applied to a
realistic autonomous-systems use case rather than a toy example.

---

## Table of Contents
- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [The OODA Loop](#the-ooda-loop)
- [Decision Confidence Score (DCS)](#decision-confidence-score-dcs)
- [Design Patterns Used](#design-patterns-used)
- [Project Structure](#project-structure)
- [Building](#building)
- [Running the Simulation](#running-the-simulation)
- [Running the Tests](#running-the-tests)
- [Sample Output](#sample-output)
- [Extending the Project](#extending-the-project)
- [Known Limitations](#known-limitations)

---

## Overview

Traditional security systems often act as black boxes — an alert fires, an
action happens, and the reasoning is opaque. AgentSec++ takes the opposite
approach: every decision the agent makes is backed by an explicit,
numerically-scored justification, following the classical **Observe →
Orient → Decide → Act** (OODA) loop used in real autonomous systems and
cybersecurity research.

The agent is deliberately architected so its core decision logic (currently
rule-based) can later be swapped for a machine-learned model, an LLM-backed
reasoner, or a formally verifiable decision module — without changing the
surrounding class structure. This makes it a reusable research/teaching
platform, not just a one-off script.

## Key Features

- **Polymorphic event handling** — four distinct security event types
  processed through a common interface
- **Pluggable response actions** — block, notify, quarantine, or ignore,
  selected dynamically at runtime
- **Explainable decisions** — every action comes with a human-readable
  reason and a numeric confidence score (0.0–1.0)
- **Configurable caution levels** — Strict / Balanced / Relaxed strategies
  change how aggressively the agent responds, without touching engine code
- **Dual logging** — simultaneous human-readable text logs and
  machine-readable JSON logs
- **Unit-tested decision logic** — core behaviors verified with a
  lightweight assertion-based test suite

## Architecture

```
SecurityEvent (abstract)
├── LoginFailure       — tracks failed login attemptCount
├── PortScan           — tracks portsScanned
├── FileTampering      — tracks filePath
└── MalwareAlert       — tracks malware signature

Action (abstract)
├── BlockIP
├── Ignore
├── NotifyAdmin
└── QuarantineDevice

Rule (abstract)
├── LoginRule            → matches LoginFailure events
├── PortScanRule         → matches PortScan events
├── FileTamperingRule    → matches FileTampering events
└── MalwareRule          → matches MalwareAlert events

DecisionStrategy (abstract)
├── StrictStrategy     — low thresholds, blocks more readily
├── BalancedStrategy   — default, moderate caution
└── RelaxedStrategy    — high thresholds, blocks less readily

Logger (abstract)
├── TextLogger   — appends human-readable lines to a .txt file
└── JSONLogger   — writes a structured JSON array of decisions

DecisionEngine   — evaluates rules against an event, computes DCS,
                   selects an Action based on the active strategy
SecurityAgent    — orchestrates the full OODA loop per event
EventFactory     — centralizes event object creation from raw input
```

## The OODA Loop

Each event flows through the agent as follows:

```
Observe   →  SecurityAgent.observe(event)         stores the incoming event
Orient    →  event->display()                     surfaces event details
Decide    →  DecisionEngine->decide(event)         evaluates rules, computes DCS,
                                                     selects an Action
Act       →  action->execute()                     performs the response
Explain   →  explainDecision()                     prints the reason + confidence
Record    →  Logger->log(...)                      persists the decision
```

## Decision Confidence Score (DCS)

Rather than a hard-coded if/else chain, every decision is backed by a
weighted confidence score:

```
DCS = 0.35 × Severity
    + 0.25 × RuleMatchStrength
    + 0.20 × HistoricalFrequency
    + 0.20 × SourceReputation
```

| Factor              | Weight | Meaning                                                    |
|---------------------|--------|--------------------------------------------------------------|
| Severity            | 0.35   | The event's own severity rating (0–10), normalized to 0–1   |
| Rule Match Strength | 0.25   | How strongly the matched rule's condition was met            |
| Historical Frequency| 0.20   | How often this source IP has triggered events this session   |
| Source Reputation   | 0.20   | A per-IP trust score; defaults to 0.5 (neutral) if unknown    |

The resulting score is compared against the active strategy's thresholds:

| DCS Range        | Balanced Strategy Action |
|-------------------|---------------------------|
| ≥ 0.85            | Block / Quarantine        |
| 0.60 – 0.85       | Notify Administrator      |
| < 0.60            | Monitor / Ignore          |

Thresholds shift depending on whether `StrictStrategy`, `BalancedStrategy`,
or `RelaxedStrategy` is active.

## Design Patterns Used

**Factory Pattern** — `EventFactory::createEvent(...)` centralizes object
creation from raw CSV input, so calling code never directly instantiates a
concrete event type. Adding a new event type only requires a change in one
place.

**Strategy Pattern** — `DecisionEngine` holds a `DecisionStrategy*` and asks
it for thresholds rather than hard-coding them. Swapping the active
strategy changes the agent's overall caution level without modifying
`DecisionEngine` itself.

## Project Structure

```
agentsec-plus-plus/
├── README.md
├── .gitignore
├── main.cpp                    simulation entry point
├── include/                    class headers
│   ├── SecurityEvent.h / LoginFailure.h / PortScan.h / ...
│   ├── Action.h / BlockIP.h / Ignore.h / ...
│   ├── Rule.h / LoginRule.h / FileTamperingRule.h / ...
│   ├── DecisionStrategy.h
│   ├── DecisionEngine.h
│   ├── SecurityAgent.h
│   ├── Logger.h
│   └── EventFactory.h
├── src/                        .cpp implementations
│   ├── SecurityEvent.cpp
│   └── DecisionEngine.cpp
├── tests/
│   └── test_engine.cpp         unit tests for decision logic
├── data/
│   └── sample_events.txt       sample simulation input
└── docs/
    ├── project-proposal.md
    ├── architecture.md
    └── commit-plan.md
```

## Building

Requires a C++17-capable compiler (g++ 7+, clang, or MSVC).

```bash
g++ -std=c++17 -Iinclude main.cpp src/SecurityEvent.cpp src/DecisionEngine.cpp -o agentsec
```

On Windows, this produces `agentsec.exe`.

## Running the Simulation

```bash
./agentsec data/sample_events.txt      # Linux/Mac
agentsec.exe data\sample_events.txt    # Windows
```

Output is printed to the console and written to `agent_log.txt` (human-readable)
and `agent_log.json` (structured).

Input format (`data/sample_events.txt`), one event per line:
```
type,ip,severity,description,extra
login_fail,192.168.1.10,6,Repeated login failures,7
```
Valid `type` values: `login_fail`, `port_scan`, `file_tamper`, `malware`.

## Running the Tests

```bash
g++ -std=c++17 -Iinclude tests/test_engine.cpp src/SecurityEvent.cpp src/DecisionEngine.cpp -o run_tests
./run_tests
```

Expected output: `6/6 tests passed.`

## Sample Output

```
[MalwareAlert] Signature: TrojanX.Gen | Severity: 9
[ACTION] Quarantining device: 172.16.0.9
  -> Explanation: Rule=MalwareRule DCS=0.705 Strategy=Balanced | Confidence: 0.705
```

## Extending the Project

- Add a new event type: create a class extending `SecurityEvent`, register
  it in `EventFactory`
- Add a new response: create a class extending `Action`
- Add a new detection rule: create a class extending `Rule`, register it
  with `DecisionEngine::addRule()` in `main.cpp`
- Tune the DCS weights or thresholds: edit `DecisionEngine::computeDCS()`
  or the relevant `DecisionStrategy` subclass

## Known Limitations

- Historical frequency and source reputation are in-memory only and reset
  each run (no persistence layer)
- Severity is supplied directly in the input data rather than derived from
  raw signal analysis
- This is a research/educational simulation — it does not integrate with
  any real firewall, IDS, or live network traffic
