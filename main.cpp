#include "SecurityEvent.h"
#include "EventFactory.h"
#include "Rule.h"
#include "LoginRule.h"
#include "PortScanRule.h"
#include "MalwareRule.h"
#include "FileTamperingRule.h"
#include "DecisionEngine.h"
#include "DecisionStrategy.h"
#include "Logger.h"
#include "SecurityAgent.h"

#include <fstream>
#include <sstream>
#include <iostream>
#include <vector>

// Splits a CSV line on commas
static std::vector<std::string> split(const std::string& line, char delim) {
    std::vector<std::string> tokens;
    std::stringstream ss(line);
    std::string item;
    while (std::getline(ss, item, delim)) tokens.push_back(item);
    return tokens;
}

int main(int argc, char* argv[]) {
    std::string dataFile = "data/sample_events.txt";
    if (argc > 1) dataFile = argv[1];

    BalancedStrategy strategy;
    DecisionEngine engine(&strategy);
    engine.addRule(new LoginRule(5));
    engine.addRule(new PortScanRule(10));
    engine.addRule(new MalwareRule());
    engine.addRule(new FileTamperingRule());

    TextLogger textLogger("agent_log.txt");
    JSONLogger jsonLogger("agent_log.json");
    SecurityAgent agent(&engine, {&textLogger, &jsonLogger});

    std::ifstream file(dataFile);
    if (!file.is_open()) {
        std::cerr << "Could not open data file: " << dataFile << std::endl;
        return 1;
    }

    std::string line;
    int lineNum = 0;
    while (std::getline(file, line)) {
        lineNum++;
        if (line.empty() || line[0] == '#') continue;

        std::vector<std::string> fields = split(line, ',');
        if (fields.size() < 5) {
            std::cerr << "Skipping malformed line " << lineNum << ": " << line << std::endl;
            continue;
        }

        try {
            SecurityEvent* event = EventFactory::createEvent(
                fields[0], fields[1], std::stoi(fields[2]), fields[3], fields[4]);
            agent.observe(event);
            agent.processLatest();
        } catch (const std::exception& ex) {
            std::cerr << "Error processing line " << lineNum << ": " << ex.what() << std::endl;
        }
    }

    std::cout << "Simulation complete. See agent_log.txt for full log." << std::endl;
    return 0;
}
