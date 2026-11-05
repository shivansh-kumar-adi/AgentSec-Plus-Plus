#ifndef DECISION_ENGINE_H
#define DECISION_ENGINE_H
#include "SecurityEvent.h"
#include "Action.h"
#include "Rule.h"
#include "DecisionStrategy.h"
#include <vector>
#include <map>
#include <string>

class DecisionEngine {
private:
    std::vector<Rule*> rules;
    DecisionStrategy* strategy;
    std::map<std::string, int> historyCount;      // per-IP event frequency
    std::map<std::string, double> reputationTable; // per-IP reputation, 0.0-1.0

    double computeDCS(const SecurityEvent* event, double ruleMatchStrength);

public:
    DecisionEngine(DecisionStrategy* strat);
    ~DecisionEngine();

    void addRule(Rule* rule);
    void setStrategy(DecisionStrategy* strat) { strategy = strat; }
    void setReputation(const std::string& ip, double score) { reputationTable[ip] = score; }

    // Returns an Action* with reason + confidence already set. Caller owns the pointer.
    Action* decide(const SecurityEvent* event);
};
#endif
