#ifndef PORT_SCAN_RULE_H
#define PORT_SCAN_RULE_H
#include "Rule.h"
#include "PortScan.h"
#include "BlockIP.h"
#include "NotifyAdmin.h"

class PortScanRule : public Rule {
private:
    int threshold;
public:
    PortScanRule(int t = 10) : threshold(t) {}

    bool matches(const SecurityEvent* event) const override {
        return event->getType() == "PortScan";
    }

    Action* getAction(const SecurityEvent* event) const override {
        const PortScan* e = dynamic_cast<const PortScan*>(event);
        if (e && e->getPortsScanned() > threshold) {
            return new BlockIP(e->getSourceIP());
        }
        return new NotifyAdmin("Port scan detected from " + event->getSourceIP());
    }

    double matchStrength(const SecurityEvent* event) const override {
        const PortScan* e = dynamic_cast<const PortScan*>(event);
        if (!e) return 0.0;
        double ratio = static_cast<double>(e->getPortsScanned()) / threshold;
        return ratio > 1.0 ? 1.0 : ratio;
    }

    std::string getName() const override { return "PortScanRule"; }
};
#endif
