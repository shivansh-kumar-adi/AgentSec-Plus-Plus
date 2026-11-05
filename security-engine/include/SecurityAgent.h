#ifndef SECURITY_AGENT_H
#define SECURITY_AGENT_H
#include "SecurityEvent.h"
#include "DecisionEngine.h"
#include "Logger.h"
#include <vector>

// Ties everything together: Observe -> Analyze -> Decide -> Act -> Explain
class SecurityAgent {
private:
    DecisionEngine* engine;
    std::vector<Logger*> loggers;
    std::vector<SecurityEvent*> observedEvents;

public:
    // Accepts one or more loggers - e.g. a TextLogger and a JSONLogger at once,
    // each producing its own output format from the same decisions.
    SecurityAgent(DecisionEngine* eng, std::vector<Logger*> logs) : engine(eng), loggers(logs) {}
    ~SecurityAgent() {
        for (SecurityEvent* e : observedEvents) delete e;
    }

    void observe(SecurityEvent* event) {
        observedEvents.push_back(event);
    }

    // Processes the most recently observed event end-to-end.
    void processLatest() {
        if (observedEvents.empty()) return;
        SecurityEvent* event = observedEvents.back();

        event->display();                          // Analyze (surface event details)
        Action* action = engine->decide(event);     // Decide

        action->execute();                          // Act
        explainDecision(event, action);             // Explain

        for (Logger* logger : loggers) {
            logger->log(event->getType(), event->getSourceIP(),
                        action->getName(), action->getReason(), action->getConfidence());
        }

        delete action;
    }

    void explainDecision(const SecurityEvent* event, const Action* action) {
        std::cout << "  -> Explanation: " << action->getReason()
                   << " | Confidence: " << action->getConfidence() << "\n" << std::endl;
    }
};
#endif
