#pragma once
// Standalone adapter for the upstream translator's diagnostics. Unsupported
// paths fail this feasibility probe instead of producing partial SPIR-V.
#include <fmt/format.h>
#include <stdexcept>
#include <type_traits>
#define LOG_TRACE(...) do {} while (0)
#define LOG_DEBUG(...) do {} while (0)
#define LOG_INFO(...) do {} while (0)
#define LOG_WARN(...) throw std::runtime_error(fmt::format(__VA_ARGS__))
#define LOG_ERROR(...) throw std::runtime_error(fmt::format(__VA_ARGS__))
#define LOG_CRITICAL(...) throw std::runtime_error(fmt::format(__VA_ARGS__))
#define LOG_TRACE_ONCE(...) LOG_TRACE(__VA_ARGS__)
#define LOG_DEBUG_ONCE(...) LOG_DEBUG(__VA_ARGS__)
#define LOG_INFO_ONCE(...) LOG_INFO(__VA_ARGS__)
#define LOG_WARN_ONCE(...) LOG_WARN(__VA_ARGS__)
#define LOG_ERROR_ONCE(...) LOG_ERROR(__VA_ARGS__)
#define LOG_CRITICAL_ONCE(...) LOG_CRITICAL(__VA_ARGS__)
template <typename T> std::string log_hex(T value) {
    return fmt::format("0x{:X}", static_cast<std::make_unsigned_t<T>>(value));
}
