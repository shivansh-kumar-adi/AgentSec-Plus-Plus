# Suggested commit plan

Add and commit files in this order, over the actual weeks you work on them —
matches the 10-phase plan. Spread across real days, don't do it all at once.

1. Initial project setup (README, .gitignore, folder structure)
2. Add SecurityEvent base class
3. Implement LoginFailure event
4. Implement PortScan event
5. Implement FileTampering and MalwareAlert events
6. Add Action interface
7. Implement BlockIP and Ignore actions
8. Implement NotifyAdmin and QuarantineDevice actions
9. Add Rule abstraction
10. Implement LoginRule
11. Implement PortScanRule and MalwareRule
12. Implement DecisionEngine (rule evaluation)
13. Add DecisionStrategy (Strategy pattern)
14. Add Decision Confidence Score calculation to DecisionEngine
15. Add SecurityAgent OODA workflow
16. Add Logger interface + TextLogger
17. Add JSONLogger
18. Implement EventFactory (Factory pattern)
19. Add sample security event dataset
20. Wire up main.cpp simulation runner
21. Handle invalid input and exceptions
22. Add unit tests
23. Fix bugs found while testing
24. Improve README / architecture docs
25. Final polish for demo
