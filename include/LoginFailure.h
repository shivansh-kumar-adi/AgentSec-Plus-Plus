#ifndef LOGIN_FAILURE_H
#define LOGIN_FAILURE_H
#include "SecurityEvent.h"
#include <iostream>

class LoginFailure : public SecurityEvent {
private:
    int attemptCount;
public:
    LoginFailure(const std::string& ip, int sev, const std::string& desc, int attempts)
        : SecurityEvent(ip, sev, desc), attemptCount(attempts) {}

    void display() const override {
        std::cout << "[LoginFailure] IP: " << sourceIP
                   << " | Attempts: " << attemptCount
                   << " | Severity: " << severity << std::endl;
    }
    std::string getType() const override { return "LoginFailure"; }
    int getAttemptCount() const { return attemptCount; }
};
#endif
