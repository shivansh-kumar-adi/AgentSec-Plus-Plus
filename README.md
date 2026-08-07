# AgentSec++

An Object-Oriented, Explainable Security Agent Framework for Autonomous Cyber Defense.

Built as a mini-project demonstrating OOP design (inheritance, polymorphism,
composition), the Factory and Strategy design patterns, and a transparent
Decision Confidence Score (DCS) model for autonomous security decision-making.

## Architecture

```
SecurityEvent (abstract)
├── LoginFailure
├── PortScan
├── FileTampering
└── MalwareAlert

Action (abstract)
├── BlockIP
├── Ignore
├── NotifyAdmin
└── QuarantineDevice

Rule (abstract)
├── LoginRule
├── PortScanRule
└── MalwareRule

DecisionStrategy (abstract)
├── StrictStrategy
├── BalancedStrategy
└── RelaxedStrategy

DecisionEngine   -- evaluates rules, computes DCS, picks an Action
SecurityAgent    -- OODA loop: observe -> analyze -> decide -> execute -> explain
Logger (abstract)
├── TextLogger
└── JSONLogger
EventFactory     -- centralizes event object creation
```

## Decision Confidence Score (DCS)

Instead of a hard-coded if/else decision, every action is backed by a
confidence score combining four weighted factors:

```
DCS = 0.35 * Severity + 0.25 * RuleMatchStrength + 0.20 * HistoricalFrequency + 0.20 * SourceReputation
```

Thresholds (Balanced strategy):
- DCS >= 0.85 -> Block
- 0.60 <= DCS < 0.85 -> Notify Administrator
- DCS < 0.60 -> Monitor / Ignore

Thresholds shift depending on the active `DecisionStrategy` (Strict, Balanced, Relaxed).

## Building

```bash
g++ -std=c++17 -Iinclude main.cpp src/SecurityEvent.cpp src/DecisionEngine.cpp -o agentsec
./agentsec data/sample_events.txt
```

Output is printed to console and written to `agent_log.txt`.

## Project layout

```
include/    class headers
src/        .cpp implementations
data/       sample event logs for simulation
tests/      unit tests
docs/       proposal and architecture notes
main.cpp    simulation entry point
```

## Status / possible extensions

- FileTampering events currently have no matching Rule (falls through to Ignore)
  — a good candidate for an added rule.
- Historical frequency and source reputation are simple in-memory maps; could
  be persisted or replaced with a real threat-intel feed.
- Decision engine is designed so the rule-based core could later be swapped
  for a learned model without changing the surrounding architecture.
