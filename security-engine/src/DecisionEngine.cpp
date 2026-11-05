#include "DecisionEngine.h"
#include "Ignore.h"
#include <sstream>

DecisionEngine::DecisionEngine(DecisionStrategy* strat) : strategy(strat) {}

DecisionEngine::~DecisionEngine() {
    for (Rule* r : rules) delete r;
}

void DecisionEngine::addRule(Rule* rule) {
    rules.push_back(rule);
}

// DCS = 0.35*Severity + 0.25*RuleMatch + 0.20*HistoricalFrequency + 0.20*SourceReputation
double DecisionEngine::computeDCS(const SecurityEvent* event, double ruleMatchStrength) {
    double S = event->getSeverity() / 10.0;               // normalize 0-10 -> 0-1
    double R = ruleMatchStrength;                          // already 0-1

    int count = ++historyCount[event->getSourceIP()];
    double H = count > 5 ? 1.0 : count / 5.0;               // normalize frequency

    double P = 0.5; // default neutral reputation if unknown
    auto it = reputationTable.find(event->getSourceIP());
    if (it != reputationTable.end()) P = it->second;

    return 0.35 * S + 0.25 * R + 0.20 * H + 0.20 * P;
}

Action* DecisionEngine::decide(const SecurityEvent* event) {
    Rule* matchedRule = nullptr;
    double bestStrength = 0.0;

    for (Rule* r : rules) {
        if (r->matches(event)) {
            double strength = r->matchStrength(event);
            if (strength >= bestStrength) {
                bestStrength = strength;
                matchedRule = r;
            }
        }
    }

    if (!matchedRule) {
        Action* fallback = new Ignore();
        fallback->setReason("No matching rule for event type: " + event->getType());
        fallback->setConfidence(0.0);
        return fallback;
    }

    double dcs = computeDCS(event, bestStrength);
    Action* action = nullptr;

    if (dcs >= strategy->blockThreshold()) {
        action = matchedRule->getAction(event);
    } else if (dcs >= strategy->notifyThreshold()) {
        // Rules are written so getAction() falls back to NotifyAdmin when
        // the "hard" threshold inside the rule itself isn't met.
        action = matchedRule->getAction(event);
    } else {
        action = new Ignore();
    }

    std::ostringstream reason;
    reason << "Rule=" << matchedRule->getName()
           << " DCS=" << dcs
           << " Strategy=" << strategy->getName();
    action->setReason(reason.str());
    action->setConfidence(dcs);

    return action;
}
