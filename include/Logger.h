#ifndef LOGGER_H
#define LOGGER_H
#include <string>
#include <fstream>
#include <stdexcept>

class Logger {
public:
    virtual void log(const std::string& eventType, const std::string& sourceIP,
                      const std::string& actionName, const std::string& reason,
                      double confidence) = 0;
    virtual ~Logger() {}
};

class TextLogger : public Logger {
private:
    std::ofstream out;
public:
    TextLogger(const std::string& filePath) {
        out.open(filePath, std::ios::app);
        if (!out.is_open()) {
            throw std::runtime_error("TextLogger: could not open " + filePath);
        }
    }
    ~TextLogger() { if (out.is_open()) out.close(); }

    void log(const std::string& eventType, const std::string& sourceIP,
             const std::string& actionName, const std::string& reason,
             double confidence) override {
        out << "[" << eventType << "] IP=" << sourceIP
            << " Action=" << actionName
            << " Confidence=" << confidence
            << " Reason=" << reason << "\n";
        out.flush();
    }
};

class JSONLogger : public Logger {
private:
    std::ofstream out;
    bool first = true;
public:
    JSONLogger(const std::string& filePath) {
        out.open(filePath, std::ios::trunc);
        if (!out.is_open()) {
            throw std::runtime_error("JSONLogger: could not open " + filePath);
        }
        out << "[\n";
    }
    ~JSONLogger() {
        if (out.is_open()) {
            out << "\n]\n";
            out.close();
        }
    }

    void log(const std::string& eventType, const std::string& sourceIP,
             const std::string& actionName, const std::string& reason,
             double confidence) override {
        if (!first) out << ",\n";
        first = false;
        out << "  {\"eventType\": \"" << eventType << "\", "
            << "\"sourceIP\": \"" << sourceIP << "\", "
            << "\"action\": \"" << actionName << "\", "
            << "\"confidence\": " << confidence << ", "
            << "\"reason\": \"" << reason << "\"}";
    }
};
#endif
