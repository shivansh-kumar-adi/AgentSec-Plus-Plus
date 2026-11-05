#include <winsock2.h>
#include <ws2tcpip.h>
#include <windows.h>
#include <tlhelp32.h>
#include <iphlpapi.h>

#include <algorithm>
#include <chrono>
#include <cstdint>
#include <iomanip>
#include <iostream>
#include <map>
#include <set>
#include <sstream>
#include <string>
#include <vector>

static std::string jsonEscape(const std::string& value) {
    std::ostringstream out;
    for (unsigned char c : value) {
        switch (c) {
            case '"': out << "\\\""; break;
            case '\\': out << "\\\\"; break;
            case '\b': out << "\\b"; break;
            case '\f': out << "\\f"; break;
            case '\n': out << "\\n"; break;
            case '\r': out << "\\r"; break;
            case '\t': out << "\\t"; break;
            default:
                if (c < 0x20) out << "\\u" << std::hex << std::setw(4) << std::setfill('0') << int(c);
                else out << c;
        }
    }
    return out.str();
}

static std::string utcNow() {
    SYSTEMTIME now{};
    GetSystemTime(&now);
    char result[32];
    std::snprintf(result, sizeof(result), "%04u-%02u-%02uT%02u:%02u:%02u.%03uZ",
                  now.wYear, now.wMonth, now.wDay, now.wHour, now.wMinute, now.wSecond, now.wMilliseconds);
    return result;
}

static std::string eventId(const std::string& kind, std::uint64_t discriminator) {
    LARGE_INTEGER counter{};
    QueryPerformanceCounter(&counter);
    std::ostringstream value;
    value << kind << '-' << GetCurrentProcessId() << '-' << counter.QuadPart << '-' << discriminator;
    return value.str();
}

static std::string ipv4(DWORD networkOrder) {
    IN_ADDR address{};
    address.S_un.S_addr = networkOrder;
    char buffer[INET_ADDRSTRLEN]{};
    return inet_ntop(AF_INET, &address, buffer, sizeof(buffer)) ? buffer : "0.0.0.0";
}

static void emitProcessSnapshot() {
    HANDLE snapshot = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    if (snapshot == INVALID_HANDLE_VALUE) {
        std::cerr << "CreateToolhelp32Snapshot failed: " << GetLastError() << '\n';
        return;
    }
    PROCESSENTRY32W entry{};
    entry.dwSize = sizeof(entry);
    if (Process32FirstW(snapshot, &entry)) {
        do {
            int size = WideCharToMultiByte(CP_UTF8, WC_ERR_INVALID_CHARS, entry.szExeFile, -1, nullptr, 0, nullptr, nullptr);
            std::string image(size > 0 ? static_cast<size_t>(size) : 0, '\0');
            if (size > 1) {
                WideCharToMultiByte(CP_UTF8, WC_ERR_INVALID_CHARS, entry.szExeFile, -1, image.data(), size, nullptr, nullptr);
                image.pop_back();
            }
            std::cout << "{\"event_id\":\"" << eventId("proc", entry.th32ProcessID)
                      << "\",\"event_type\":\"process\",\"occurred_at\":\"" << utcNow()
                      << "\",\"severity\":1,\"process_id\":" << entry.th32ProcessID
                      << ",\"description\":\"Process observed\",\"attributes\":{\"image\":\""
                      << jsonEscape(image) << "\",\"parent_process_id\":" << entry.th32ParentProcessID
                      << ",\"thread_count\":" << entry.cntThreads << "}}\n";
        } while (Process32NextW(snapshot, &entry));
    }
    CloseHandle(snapshot);
}

static void emitTcpSnapshot() {
    ULONG bytes = 0;
    DWORD sizeResult = GetTcpTable2(nullptr, &bytes, FALSE);
    if (sizeResult != ERROR_INSUFFICIENT_BUFFER) {
        std::cerr << "Unable to size TCP table: " << sizeResult << '\n';
        return;
    }
    std::vector<unsigned char> storage(bytes);
    auto* table = reinterpret_cast<PMIB_TCPTABLE2>(storage.data());
    if (GetTcpTable2(table, &bytes, FALSE) != NO_ERROR) {
        std::cerr << "Unable to read TCP table\n";
        return;
    }
    std::map<std::string, std::set<unsigned short>> inboundPorts;
    for (DWORD index = 0; index < table->dwNumEntries; ++index) {
        const auto& row = table->table[index];
        const std::string local = ipv4(row.dwLocalAddr);
        const std::string remote = ipv4(row.dwRemoteAddr);
        const auto localPort = ntohs(static_cast<u_short>(row.dwLocalPort));
        const auto remotePort = ntohs(static_cast<u_short>(row.dwRemotePort));
        std::cout << "{\"event_id\":\"" << eventId("tcp", index)
                  << "\",\"event_type\":\"network_connection\",\"occurred_at\":\"" << utcNow()
                  << "\",\"severity\":2,\"source_ip\":\"" << jsonEscape(remote)
                  << "\",\"process_id\":" << row.dwOwningPid
                  << ",\"description\":\"TCP endpoint observed\",\"attributes\":{\"local_ip\":\""
                  << jsonEscape(local) << "\",\"local_port\":" << localPort << ",\"remote_port\":"
                  << remotePort << ",\"tcp_state\":" << row.dwState << "}}\n";
        if (remote != "0.0.0.0" && row.dwState != MIB_TCP_STATE_LISTEN) inboundPorts[remote].insert(localPort);
    }
    for (const auto& [remote, ports] : inboundPorts) {
        if (ports.size() < 10) continue;
        std::cout << "{\"event_id\":\"" << eventId("portscan", ports.size())
                  << "\",\"event_type\":\"detection\",\"occurred_at\":\"" << utcNow()
                  << "\",\"severity\":7,\"source_ip\":\"" << jsonEscape(remote)
                  << "\",\"description\":\"Potential port scan: remote endpoint reached multiple local ports\""
                  << ",\"attributes\":{\"detector\":\"distinct_local_ports\",\"port_count\":" << ports.size()
                  << ",\"confirmed_indicator\":false}}\n";
    }
}

int main(int argc, char** argv) {
    bool once = false;
    unsigned intervalSeconds = 30;
    for (int i = 1; i < argc; ++i) {
        const std::string arg = argv[i];
        if (arg == "--once") once = true;
        else if (arg == "--interval" && i + 1 < argc) intervalSeconds = std::max(5u, static_cast<unsigned>(std::stoul(argv[++i])));
    }
    do {
        emitProcessSnapshot();
        emitTcpSnapshot();
        std::cout.flush();
        if (!once) Sleep(intervalSeconds * 1000);
    } while (!once);
    return 0;
}
