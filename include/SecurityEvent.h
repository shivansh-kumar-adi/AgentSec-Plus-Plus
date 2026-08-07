#ifndef SECURITY_EVENT_H
#define SECURITY_EVENT_H
#include <string>
#include <ctime>

class SecurityEvent {
protected:
    std::string sourceIP;
    std::string timestamp;
    int severity;
    std::string description;

public:
    SecurityEvent(const std::string& ip, int sev, const std::string& desc);
    virtual ~SecurityEvent() {}

    virtual void display() const = 0;
    virtual std::string getType() const = 0;

    std::string getSourceIP() const { return sourceIP; }
    int getSeverity() const { return severity; }
    std::string getTimestamp() const { return timestamp; }
    std::string getDescription() const { return description; }
};
#endif
