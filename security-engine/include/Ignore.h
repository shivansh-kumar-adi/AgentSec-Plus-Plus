#ifndef IGNORE_H
#define IGNORE_H
#include "Action.h"
#include <iostream>

class Ignore : public Action {
public:
    void execute() override {
        std::cout << "[ACTION] Event ignored (low severity)." << std::endl;
    }
    std::string getName() const override { return "Ignore"; }
};
#endif
