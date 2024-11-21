/**
 * @file stdafx.cpp
 * @brief File di implementazione per la precompilazione degli header
 */

#include "stdafx.h"

// Librerie Windows necessarie
#ifdef _WIN32
    #pragma comment(lib, "ws2_32.lib")      // Supporto di rete Windows
    #pragma comment(lib, "wbemuuid.lib")    // Windows Management Instrumentation
    #pragma comment(lib, "userenv.lib")     // Funzioni dell'ambiente utente
    #pragma comment(lib, "shlwapi.lib")     // Funzioni di utilità della shell
    #pragma comment(lib, "version.lib")     // Funzioni di versione
    #pragma comment(lib, "psapi.lib")       // Process Status API
    #pragma comment(lib, "iphlpapi.lib")    // IP Helper API
    #pragma comment(lib, "wtsapi32.lib")    // Windows Terminal Services
    #pragma comment(lib, "pdh.lib")         // Performance Data Helper
    #pragma comment(lib, "netapi32.lib")    // Network Management
    #pragma comment(lib, "advapi32.lib")    // Advanced Windows 32 Base API
    #pragma comment(lib, "ole32.lib")       // Object Linking and Embedding
    #pragma comment(lib, "oleaut32.lib")    // OLE Automation
    #pragma comment(lib, "uuid.lib")        // UUID Generation
    #pragma comment(lib, "shell32.lib")     // Shell API
    #pragma comment(lib, "user32.lib")      // User Interface
    #pragma comment(lib, "gdi32.lib")       // Graphics Device Interface
    #pragma comment(lib, "kernel32.lib")    // Windows NT Kernel
#endif

/**
 * @class ComInitializer
 * @brief Gestisce l'inizializzazione e la chiusura di COM
 */
class ComInitializer {
public:
    ComInitializer() {
        HRESULT hr = CoInitializeEx(nullptr, COINIT_MULTITHREADED);
        if (FAILED(hr)) {
            throw std::runtime_error("Impossibile inizializzare COM");
        }
    }

    ~ComInitializer() {
        CoUninitialize();
    }

    ComInitializer(const ComInitializer&) = delete;
    ComInitializer& operator=(const ComInitializer&) = delete;
};

/**
 * @class WinsockInitializer
 * @brief Gestisce l'inizializzazione e la chiusura di Winsock
 */
class WinsockInitializer {
public:
    WinsockInitializer() {
        WSADATA wsaData;
        if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
            throw std::runtime_error("Impossibile inizializzare Winsock");
        }
    }

    ~WinsockInitializer() {
        WSACleanup();
    }

    WinsockInitializer(const WinsockInitializer&) = delete;
    WinsockInitializer& operator=(const WinsockInitializer&) = delete;
};

// Istanze globali per l'inizializzazione
namespace {
    ComInitializer g_comInitializer;
    WinsockInitializer g_winsockInitializer;
}

/**
 * @brief Gestisce le eccezioni non gestite nell'applicazione
 * @param exceptionInfo Informazioni sull'eccezione
 */
static LONG WINAPI CustomUnhandledExceptionHandler(EXCEPTION_POINTERS* exceptionInfo) {
    // Prepara il messaggio di errore
    std::stringstream errorStream;
    errorStream << "Errore non gestito rilevato\n";
    errorStream << "Codice eccezione: 0x" << std::hex << exceptionInfo->ExceptionRecord->ExceptionCode << "\n";
    errorStream << "Indirizzo: 0x" << std::hex << exceptionInfo->ExceptionRecord->ExceptionAddress << "\n";

    // Qui si potrebbe aggiungere il logging dell'errore
    // o altre azioni di gestione degli errori

    // Termina il processo in modo controllato
    ExitProcess(1);
    return EXCEPTION_EXECUTE_HANDLER;
}

/**
 * @brief Punto di ingresso della DLL
 * @param hModule Handle del modulo
 * @param ul_reason_for_call Ragione della chiamata
 * @param lpReserved Riservato
 * @return TRUE se l'inizializzazione ha successo
 */
BOOL APIENTRY DllMain(HMODULE hModule, DWORD ul_reason_for_call, LPVOID) {
    switch (ul_reason_for_call) {
        case DLL_PROCESS_ATTACH: {
            // Disabilita le notifiche di thread per migliorare le performance
            DisableThreadLibraryCalls(hModule);

            // Imposta il gestore delle eccezioni personalizzato
            SetUnhandledExceptionFilter(CustomUnhandledExceptionHandler);

            // Inizializza il sistema di logging
            // TODO: Implementare l'inizializzazione del logging

            break;
        }

        case DLL_PROCESS_DETACH: {
            // Esegui la pulizia necessaria
            // TODO: Implementare la pulizia delle risorse

            break;
        }

        case DLL_THREAD_ATTACH:
        case DLL_THREAD_DETACH:
            // Non facciamo nulla qui poiché abbiamo disabilitato le notifiche di thread
            break;
    }

    return TRUE;
}
