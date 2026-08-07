// Simple assertion-based unit tests — no external framework needed.
// Compile separately from main.cpp:
//   g++ -std=c++17 -Iinclude tests/test_engine.cpp src/SecurityEvent.cpp src/DecisionEngine.cpp -o run_tests
//   ./run_tests

#include "SecurityEvent.h"
#include "LoginFailure.h"
#include "PortScan.h"
#include "MalwareAlert.h"
#include "LoginRule.h"
#include "PortScanRule.h"
#include "MalwareRule.h"
#include "FileTampering.h"
#include "FileTamperingRule.h"
#include "DecisionEngine.h"
#include "DecisionStrategy.h"
#include "Action.h"

#include <iostream>
#include <cassert>

int testsRun = 0;
int testsPassed = 0;

void check(bool condition, const std::string& testName) {
    testsRun++;
    if (condition) {
        testsPassed++;
        std::cout << "[PASS] " << testName << std::endl;
    } else {
        std::cout << "[FAIL] " << testName << std::endl;
    }
}

void test_low_attempt_login_is_not_blocked() {
    BalancedStrategy strategy;
    DecisionEngine engine(&strategy);
    engine.addRule(new LoginRule(5));

    LoginFailure event("1.2.3.4", 2, "test", 1); // low severity, low attempts
    Action* action = engine.decide(&event);

    check(action->getName() != "BlockIP", "Low-severity single login failure should not be blocked");
    delete action;
}

void test_high_attempt_login_gets_blocked_eventually() {
    BalancedStrategy strategy;
    DecisionEngine engine(&strategy);
    engine.addRule(new LoginRule(5));

    // Simulate repeated high-severity failed logins from the same IP —
    // historical frequency factor should push DCS up over calls.
    Action* lastAction = nullptr;
    for (int i = 0; i < 6; i++) {
        LoginFailure event("9.9.9.9", 9, "test", 8); // high severity, high attempts
        delete lastAction;
        lastAction = engine.decide(&event);
    }

    check(lastAction->getName() == "BlockIP",
          "Repeated high-severity login failures should eventually trigger BlockIP");
    delete lastAction;
}

void test_malware_always_quarantines() {
    BalancedStrategy strategy;
    DecisionEngine engine(&strategy);
    engine.addRule(new MalwareRule());

    MalwareAlert event("5.5.5.5", 9, "test", "TrojanX");
    Action* action = engine.decide(&event);

    check(action->getName() == "QuarantineDevice", "Malware alert should trigger quarantine");
    delete action;
}

void test_unmatched_event_falls_back_to_ignore() {
    BalancedStrategy strategy;
    DecisionEngine engine(&strategy); // no rules added

    PortScan event("8.8.8.8", 5, "test", 20);
    Action* action = engine.decide(&event);

    check(action->getName() == "Ignore", "Event with no matching rule should default to Ignore");
    delete action;
}

void test_high_severity_file_tampering_quarantines() {
    BalancedStrategy strategy;
    DecisionEngine engine(&strategy);
    engine.addRule(new FileTamperingRule());

    FileTampering event("192.168.1.22", 8, "test", "/etc/passwd");
    Action* action = engine.decide(&event);

    check(action->getName() == "QuarantineDevice",
          "High-severity file tampering should trigger quarantine");
    delete action;
}

void test_strict_strategy_blocks_more_easily_than_relaxed() {
    StrictStrategy strict;
    RelaxedStrategy relaxed;

    check(strict.blockThreshold() < relaxed.blockThreshold(),
          "Strict strategy should have a lower block threshold than Relaxed");
}

int main() {
    test_low_attempt_login_is_not_blocked();
    test_high_attempt_login_gets_blocked_eventually();
    test_malware_always_quarantines();
    test_unmatched_event_falls_back_to_ignore();
    test_high_severity_file_tampering_quarantines();
    test_strict_strategy_blocks_more_easily_than_relaxed();

    std::cout << "\n" << testsPassed << "/" << testsRun << " tests passed." << std::endl;
    return (testsPassed == testsRun) ? 0 : 1;
}
