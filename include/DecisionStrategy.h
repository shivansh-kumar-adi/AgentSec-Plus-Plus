#ifndef DECISION_STRATEGY_H
#define DECISION_STRATEGY_H
#include <string>

// Strategy pattern: controls how "cautious" the agent is by shifting
// the DCS thresholds used to pick an action.
class DecisionStrategy {
public:
    virtual double blockThreshold() const = 0;
    virtual double notifyThreshold() const = 0;
    virtual std::string getName() const = 0;
    virtual ~DecisionStrategy() {}
};

class StrictStrategy : public DecisionStrategy {
public:
    double blockThreshold() const override { return 0.70; }
    double notifyThreshold() const override { return 0.45; }
    std::string getName() const override { return "Strict"; }
};

class BalancedStrategy : public DecisionStrategy {
public:
    double blockThreshold() const override { return 0.85; }
    double notifyThreshold() const override { return 0.60; }
    std::string getName() const override { return "Balanced"; }
};

class RelaxedStrategy : public DecisionStrategy {
public:
    double blockThreshold() const override { return 0.95; }
    double notifyThreshold() const override { return 0.75; }
    std::string getName() const override { return "Relaxed"; }
};
#endif
