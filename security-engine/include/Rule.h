#ifndef RULE_H
#define RULE_H
#include "SecurityEvent.h"
#include "Action.h"
#include <string>

class Rule {
public:
    // Returns true if this rule applies to the given event
    virtual bool matches(const SecurityEvent* event) const = 0;

    // Returns a newly-created Action* if matches() is true (caller owns the pointer)
    virtual Action* getAction(const SecurityEvent* event) const = 0;

    // How strongly the rule matched, 0.0-1.0 (used in DCS calculation)
    virtual double matchStrength(const SecurityEvent* event) const = 0;

    virtual std::string getName() const = 0;
    virtual ~Rule() {}
};
#endif
