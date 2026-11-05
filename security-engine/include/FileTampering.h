#ifndef FILE_TAMPERING_H
#define FILE_TAMPERING_H
#include "SecurityEvent.h"
#include <iostream>

class FileTampering : public SecurityEvent {
private:
    std::string filePath;
public:
    FileTampering(const std::string& ip, int sev, const std::string& desc, const std::string& path)
        : SecurityEvent(ip, sev, desc), filePath(path) {}

    void display() const override {
        std::cout << "[FileTampering] File: " << filePath
                   << " | Severity: " << severity << std::endl;
    }
    std::string getType() const override { return "FileTampering"; }
    std::string getFilePath() const { return filePath; }
};
#endif
