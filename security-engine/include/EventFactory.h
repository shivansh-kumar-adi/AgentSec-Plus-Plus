#ifndef EVENT_FACTORY_H
#define EVENT_FACTORY_H
#include "SecurityEvent.h"
#include "LoginFailure.h"
#include "PortScan.h"
#include "FileTampering.h"
#include "MalwareAlert.h"
#include <string>
#include <stdexcept>
#include <sstream>

// Factory pattern: centralizes event creation so callers never use `new`
// directly on a concrete event type. Makes it easy to add new event types
// later without touching calling code.
class EventFactory {
public:
    // type examples: "login_fail", "port_scan", "file_tamper", "malware"
    // extra: an extra numeric/string parameter specific to that event type
    static SecurityEvent* createEvent(const std::string& type, const std::string& ip,
                                       int severity, const std::string& desc,
                                       const std::string& extra) {
        if (type == "login_fail") {
            int attempts = extra.empty() ? 1 : std::stoi(extra);
            return new LoginFailure(ip, severity, desc, attempts);
        }
        if (type == "port_scan") {
            int ports = extra.empty() ? 1 : std::stoi(extra);
            return new PortScan(ip, severity, desc, ports);
        }
        if (type == "file_tamper") {
            return new FileTampering(ip, severity, desc, extra);
        }
        if (type == "malware") {
            return new MalwareAlert(ip, severity, desc, extra);
        }
        throw std::invalid_argument("EventFactory: unknown event type '" + type + "'");
    }
};
#endif
