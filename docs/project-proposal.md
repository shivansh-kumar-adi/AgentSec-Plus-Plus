# Project Proposal: AgentSec++

## Title
AgentSec++: An Object-Oriented Explainable Security Agent Framework for
Autonomous Cyber Defense

## Motivation
Most introductory OOP projects use toy examples (banking systems, library
management) that don't connect to real-world autonomous systems. This
project instead builds a rule-based security agent that follows the
classical Observe-Orient-Decide-Act (OODA) loop used in real autonomous
cyber-defense systems, while staying approachable for a 2nd-year OOP course.

## Objectives
- Apply core OOP principles (inheritance, polymorphism, encapsulation,
  composition) to a realistic multi-class system
- Implement two standard design patterns (Factory, Strategy) in a context
  where they solve a real problem, not as an isolated exercise
- Produce an agent whose decisions are explainable, not just correct -
  every action comes with a stated reason and a numeric confidence score
- Build and test the system incrementally, with meaningful Git history
  documenting the process

## Scope
The agent processes a fixed set of security event types (login failures,
port scans, file tampering, malware alerts) against a small rule set, and
outputs an action with a confidence score for each. It runs against a
static input file for the mini-project demonstration - it is not connected
to any live network traffic or real firewall.

## Deliverables
- Working C++17 codebase (event, action, rule, decision-engine layers)
- Decision Confidence Score (DCS) model combining severity, rule strength,
  event history, and source reputation
- Unit tests covering the decision logic
- Text and JSON logging of all decisions
- Simulation runner over a sample event dataset
- This documentation set

## Future extensions
The decision engine is deliberately decoupled from the rule-matching logic,
so a future cohort could replace the rule-based core with a learned model
(e.g. a simple classifier) without changing the surrounding agent
architecture.
