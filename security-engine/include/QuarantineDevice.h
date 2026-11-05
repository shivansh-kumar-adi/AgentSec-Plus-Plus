#ifndef QUARANTINE_DEVICE_H
#define QUARANTINE_DEVICE_H
#include "Action.h"
#include <iostream>

class QuarantineDevice : public Action {
private:
    std::string deviceIP;
public:
    QuarantineDevice(const std::string& ip) : deviceIP(ip) {}

    void execute() override {
        std::cout << "[ACTION] Quarantining device: " << deviceIP << std::endl;
    }
    std::string getName() const override { return "QuarantineDevice"; }
};
#endif
