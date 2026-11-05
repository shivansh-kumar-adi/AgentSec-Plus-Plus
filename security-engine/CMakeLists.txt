cmake_minimum_required(VERSION 3.20)
project(AgentSecSecurityEngine VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_library(agentsec_core src/SecurityEvent.cpp src/DecisionEngine.cpp)
target_include_directories(agentsec_core PUBLIC include)

add_executable(agentsec main.cpp)
target_link_libraries(agentsec PRIVATE agentsec_core)

add_executable(agentsec_tests tests/test_engine.cpp)
target_link_libraries(agentsec_tests PRIVATE agentsec_core)

if(WIN32)
  add_executable(agentsec_collector src/collector_windows.cpp)
  target_link_libraries(agentsec_collector PRIVATE iphlpapi ws2_32)
  target_compile_definitions(agentsec_collector PRIVATE WIN32_LEAN_AND_MEAN NOMINMAX)
endif()

enable_testing()
add_test(NAME agentsec_legacy_tests COMMAND agentsec_tests)

