# Benchmark Results - Flask vs Quart

Generated: 2025-12-08T19:44:10.438094

## Summary

This benchmark compares:
1. **Flask + WSGI** (baseline)
2. **Flask + Async routes** (trap - doesn't work)
3. **Flask + ASGI wrapper** (overhead, no benefits)
4. **Quart native** (true async)

## Main Test: 100 Concurrent Requests (/slow endpoint)

| Solution | Total Time | RPS | P95 Latency | P99 Latency |
|----------|------------|-----|-------------|-------------|
| flask-wsgi | 7.91s | 12.6 | 7.11s | 7.59s |
| flask-async-trap | 7.20s | 13.9 | 6.52s | 6.85s |
| flask-asgi-wrapper | 8.02s | 12.5 | 6.66s | 7.50s |
| quart-native | 1.27s | 78.5 | 1.07s | 1.17s |

## Key Findings

- **Flask + WSGI**: Limited by workers × threads
- **Flask + Async**: No improvement (WSGI limitation)
- **Flask + ASGI wrapper**: Worse due to overhead
- **Quart**: Massive improvement with true async

