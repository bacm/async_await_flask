# Benchmark Results - Flask vs Quart

Generated: 2025-12-09T07:19:59.341560

## Summary

This benchmark compares:
1. **Flask + WSGI** (baseline)
2. **Flask + ASGI wrapper** (overhead, no benefits)
3. **Quart native** (true async)

## Main Test: 100 Concurrent Requests (/parallel endpoint)

| Solution | Total Time | RPS | P95 Latency | P99 Latency |
|----------|------------|-----|-------------|-------------|
| flask-wsgi | 13.18s | 7.6 | 11.94s | 12.81s |
| flask-asgi-wrapper | 9.02s | 11.1 | 7.65s | 8.54s |
| quart-native | 1.38s | 72.3 | 0.94s | 1.03s |

## Key Findings

- **Flask + WSGI**: Limited by workers × threads
- **Flask + ASGI wrapper**: Worse due to overhead
- **Quart**: Massive improvement with true async

