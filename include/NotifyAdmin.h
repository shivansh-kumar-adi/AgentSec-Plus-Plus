#ifndef NOTIFY_ADMIN_H
#define NOTIFY_ADMIN_H
#include "Action.h"
#include <iostream>

class NotifyAdmin : public Action {
private:
    std::string message;
public:
    NotifyAdmin(const std::string& msg) : message(msg) {}

    void execute() override {
        std::cout << "[ACTION] Notifying admin: " << message << std::endl;
    }
    std::string getName() const override { return "NotifyAdmin"; }
};
#endif
