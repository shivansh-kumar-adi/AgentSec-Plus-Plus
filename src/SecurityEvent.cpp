#include "SecurityEvent.h"

SecurityEvent::SecurityEvent(const std::string& ip, int sev, const std::string& desc)
    : sourceIP(ip), severity(sev), description(desc) {
    time_t now = time(0);
    timestamp = ctime(&now);
}
