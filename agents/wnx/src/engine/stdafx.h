#pragma once

// Definizioni di base per Windows
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif

#ifndef NOMINMAX
#define NOMINMAX
#endif

// Windows Header Files
#include <windows.h>
#include <winsock2.h>
#include <ws2tcpip.h>
#include <shellapi.h>
#include <shlwapi.h>

// C RunTime Header Files
#include <stdlib.h>
#include <malloc.h>
#include <memory.h>
#include <tchar.h>
#include <time.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <errno.h>
#include <fcntl.h>
#include <io.h>
#include <direct.h>
#include <process.h>

// STL Header Files
#include <string>
#include <vector>
#include <map>
#include <set>
#include <algorithm>
#include <memory>
#include <chrono>
#include <filesystem>
#include <fstream>
#include <sstream>
#include <iostream>
#include <mutex>
#include <thread>
#include <atomic>
#include <regex>

// Definizioni per la gestione delle DLL
#ifdef ENGINE_EXPORTS
#define ENGINE_API __declspec(dllexport)
#else
#define ENGINE_API __declspec(dllimport)
#endif

// Namespace utilizzati di frequente
using namespace std::literals;
using namespace std::chrono_literals;
using namespace std::string_literals;

#ifdef UNICODE
typedef std::wstring tstring;
#else
typedef std::string tstring;
#endif

// Macro di utilità
#ifndef SAFE_DELETE
#define SAFE_DELETE(p) { if(p) { delete (p); (p)=nullptr; } }
#endif

#ifndef SAFE_DELETE_ARRAY
#define SAFE_DELETE_ARRAY(p) { if(p) { delete[] (p); (p)=nullptr; } }
#endif

#ifndef SAFE_RELEASE
#define SAFE_RELEASE(p) { if(p) { (p)->Release(); (p)=nullptr; } }
#endif

// Definizioni per il debug
#ifdef _DEBUG
#define VERIFY(f) assert(f)
#else
#define VERIFY(f) ((void)(f))
#endif

// Definizioni per il supporto delle stringhe
#ifdef UNICODE
#if !defined(_UNICODE)
#define _UNICODE
#endif
#endif

// Link alle librerie Windows necessarie
#pragma comment(lib, "ws2_32.lib")
#pragma comment(lib, "shlwapi.lib")
