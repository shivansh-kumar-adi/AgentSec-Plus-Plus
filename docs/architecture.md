# Architecture

## Class hierarchy

```
SecurityEvent (abstract)
├── LoginFailure      - tracks attemptCount
├── PortScan          - tracks portsScanned
├── FileTampering     - tracks filePath
└── MalwareAlert      - tracks signature

Action (abstract)
├── BlockIP
├── Ignore
├── NotifyAdmin
└── QuarantineDevice

Rule (abstract)
├── LoginRule           -> matches LoginFailure
├── PortScanRule        -> matches PortScan
├── FileTamperingRule   -> matches FileTampering
└── MalwareRule         -> matches MalwareAlert

DecisionStrategy (abstract)
├── StrictStrategy    - low thresholds, blocks more readily
├── BalancedStrategy  - default
└── RelaxedStrategy   - high thresholds, blocks less readily

Logger (abstract)
├── TextLogger  - appends human-readable lines to a .txt file
└── JSONLogger  - writes a JSON array of decision records
```

## Object collaboration

```
main.cpp
  -> EventFactory.createEvent()      builds a SecurityEvent from a CSV line
  -> SecurityAgent.observe(event)    agent stores the event
  -> SecurityAgent.processLatest()
       -> event->display()                       [Analyze]
       -> DecisionEngine->decide(event)           [Decide]
            -> for each Rule: matches() / matchStrength()
            -> computeDCS() using severity, best rule match,
               historical frequency, source reputation
            -> compares DCS against strategy thresholds
            -> matchedRule->getAction(event) builds the Action
       -> action->execute()                       [Act]
       -> explainDecision()                        [Explain]
       -> each Logger->log(...)                    [Record]
```

## Design pattern usage

**Factory Pattern** (`EventFactory`): centralizes event object creation from
raw string data so calling code never uses `new` directly on a concrete
event type. Makes adding a new event type a one-place change.

**Strategy Pattern** (`DecisionStrategy` and its subclasses): the
`DecisionEngine` holds a pointer to a `DecisionStrategy` and asks it for
block/notify thresholds rather than hard-coding them. Swapping strategies
at runtime changes how cautious the agent behaves without touching
`DecisionEngine`'s own code.

## Decision Confidence Score (DCS)

```
DCS = 0.35 * Severity + 0.25 * RuleMatchStrength
    + 0.20 * HistoricalFrequency + 0.20 * SourceReputation
```

- **Severity**: the event's own severity field (0-10), normalized to 0-1
- **RuleMatchStrength**: how strongly the matched rule's condition was
  met (e.g. attempts far past the threshold = closer to 1.0)
- **HistoricalFrequency**: how often this source IP has triggered events
  so far in the session, capped at 1.0 after 5 occurrences
- **SourceReputation**: a per-IP score (0.0-1.0); defaults to 0.5 (neutral)
  if the IP has no reputation entry

The `DecisionEngine` compares the resulting score against the active
strategy's thresholds to pick Block / Notify / Ignore-or-Monitor.

## Known limitations
- Historical frequency and reputation are in-memory only (reset each run)
- Severity is supplied directly in the input data rather than derived from
  raw signals
- No persistence layer; logs are flat files, not a database
