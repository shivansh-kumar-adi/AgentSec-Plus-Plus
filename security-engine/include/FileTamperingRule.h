#ifndef FILE_TAMPERING_RULE_H
#define FILE_TAMPERING_RULE_H
#include "Rule.h"
#include "FileTampering.h"
#include "NotifyAdmin.h"
#include "QuarantineDevice.h"

// Any modification to a tracked config/system file is treated as high-risk
// by default - file tampering rarely has a "low severity" legitimate case
// the way a single failed login might.
class FileTamperingRule : public Rule {
public:
    bool matches(const SecurityEvent* event) const override {
        return event->getType() == "FileTampering";
    }

    Action* getAction(const SecurityEvent* event) const override {
        const FileTampering* e = dynamic_cast<const FileTampering*>(event);
        if (e && e->getSeverity() >= 7) {
            return new QuarantineDevice(event->getSourceIP());
        }
        return new NotifyAdmin("File tampering detected: " +
                                (e ? e->getFilePath() : "unknown file"));
    }

    double matchStrength(const SecurityEvent* event) const override {
        // File tampering is inherently suspicious - always treat as a strong match
        return matches(event) ? 0.9 : 0.0;
    }

    std::string getName() const override { return "FileTamperingRule"; }
};
#endif
