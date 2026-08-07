#ifndef ACTION_H
#define ACTION_H
#include <string>

class Action {
protected:
    std::string reason;
    double confidence = 0.0;

public:
    virtual void execute() = 0;
    virtual std::string getName() const = 0;
    virtual void setReason(const std::string& r) { reason = r; }
    virtual std::string getReason() const { return reason; }
    virtual void setConfidence(double c) { confidence = c; }
    virtual double getConfidence() const { return confidence; }
    virtual ~Action() {}
};
#endif
