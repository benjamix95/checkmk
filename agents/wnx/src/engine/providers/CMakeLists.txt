# Provider sources
set(PROVIDER_SOURCES
    agent_plugins.cpp
    check_mk.cpp
    df.cpp
    file_monitor.cpp
    fileinfo.cpp
    internal.cpp
    logwatch_event.cpp
    mem.cpp
    mrpe.cpp
    ohm.cpp
    p_perf_counters.cpp
    perf_counters_cl.cpp
    perf_cpuload.cpp
    plugins.cpp
    ps.cpp
    services.cpp
    skype.cpp
    spool.cpp
    system_time.cpp
    wmi.cpp
)

# Provider headers
set(PROVIDER_HEADERS
    ${CMAKE_SOURCE_DIR}/include/providers/agent_plugins.h
    ${CMAKE_SOURCE_DIR}/include/providers/check_mk.h
    ${CMAKE_SOURCE_DIR}/include/providers/df.h
    ${CMAKE_SOURCE_DIR}/include/providers/file_monitor.h
    ${CMAKE_SOURCE_DIR}/include/providers/fileinfo.h
    ${CMAKE_SOURCE_DIR}/include/providers/internal.h
    ${CMAKE_SOURCE_DIR}/include/providers/logwatch_event.h
    ${CMAKE_SOURCE_DIR}/include/providers/mem.h
    ${CMAKE_SOURCE_DIR}/include/providers/mrpe.h
    ${CMAKE_SOURCE_DIR}/include/providers/ohm.h
    ${CMAKE_SOURCE_DIR}/include/providers/p_perf_counters.h
    ${CMAKE_SOURCE_DIR}/include/providers/perf_counters_cl.h
    ${CMAKE_SOURCE_DIR}/include/providers/perf_cpuload.h
    ${CMAKE_SOURCE_DIR}/include/providers/plugins.h
    ${CMAKE_SOURCE_DIR}/include/providers/ps.h
    ${CMAKE_SOURCE_DIR}/include/providers/services.h
    ${CMAKE_SOURCE_DIR}/include/providers/skype.h
    ${CMAKE_SOURCE_DIR}/include/providers/spool.h
    ${CMAKE_SOURCE_DIR}/include/providers/system_time.h
    ${CMAKE_SOURCE_DIR}/include/providers/wmi.h
)

add_library(providers STATIC ${PROVIDER_SOURCES} ${PROVIDER_HEADERS})
target_include_directories(providers PUBLIC ${CMAKE_SOURCE_DIR}/include)
