#ifndef BLOCK_IP_H
#define BLOCK_IP_H
#include "Action.h"
#include <iostream>

class BlockIP : public Action {
private:
    std::string targetIP;
public:
    BlockIP(const std::string& ip) : targetIP(ip) {}

    void execute() override {
        std::cout << "[ACTION] Blocking IP: " << targetIP << std::endl;
    }
    std::string getName() const override { return "BlockIP"; }
};
#endif
