#ifndef PORT_SCAN_H
#define PORT_SCAN_H
#include "SecurityEvent.h"
#include <iostream>

class PortScan : public SecurityEvent {
private:
    int portsScanned;
public:
    PortScan(const std::string& ip, int sev, const std::string& desc, int ports)
        : SecurityEvent(ip, sev, desc), portsScanned(ports) {}

    void display() const override {
        std::cout << "[PortScan] IP: " << sourceIP
                   << " | Ports scanned: " << portsScanned
                   << " | Severity: " << severity << std::endl;
    }
    std::string getType() const override { return "PortScan"; }
    int getPortsScanned() const { return portsScanned; }
};
#endif
