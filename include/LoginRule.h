#ifndef LOGIN_RULE_H
#define LOGIN_RULE_H
#include "Rule.h"
#include "LoginFailure.h"
#include "BlockIP.h"
#include "NotifyAdmin.h"

class LoginRule : public Rule {
private:
    int threshold;
public:
    LoginRule(int t = 5) : threshold(t) {}

    bool matches(const SecurityEvent* event) const override {
        return event->getType() == "LoginFailure";
    }

    Action* getAction(const SecurityEvent* event) const override {
        const LoginFailure* e = dynamic_cast<const LoginFailure*>(event);
        if (e && e->getAttemptCount() > threshold) {
            return new BlockIP(e->getSourceIP());
        }
        return new NotifyAdmin("Repeated login failures from " + event->getSourceIP());
    }

    double matchStrength(const SecurityEvent* event) const override {
        const LoginFailure* e = dynamic_cast<const LoginFailure*>(event);
        if (!e) return 0.0;
        double ratio = static_cast<double>(e->getAttemptCount()) / threshold;
        return ratio > 1.0 ? 1.0 : ratio;
    }

    std::string getName() const override { return "LoginRule"; }
};
#endif
