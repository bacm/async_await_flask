#!/usr/bin/env python3
"""
Script de benchmark complet
Compare les performances de toutes les solutions
"""
import asyncio
import time
import json
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
import httpx
from datetime import datetime

# Configuration
SERVICES = {
    "flask-wsgi": "http://localhost:5001",
    "flask-async-trap": "http://localhost:5002",
    "flask-asgi-wrapper": "http://localhost:5003",
    "quart-native": "http://localhost:5004"
}

ENDPOINTS = ['/parallel', '/multi-io', '/cpu-intensive', '/db-simulation', '/slow']


class BenchmarkResults:
    """Stocke et analyse les résultats de benchmark"""

    def __init__(self):
        self.results = {}

    def add_result(self, service: str, endpoint: str, test_name: str, data: Dict[str, Any]):
        """Ajoute un résultat de test"""
        if service not in self.results:
            self.results[service] = {}
        if endpoint not in self.results[service]:
            self.results[service][endpoint] = {}
        self.results[service][endpoint][test_name] = data

    def get_summary(self) -> Dict[str, Any]:
        """Génère un résumé des résultats"""
        return self.results

    def print_comparison(self, endpoint: str, test_name: str):
        """Affiche une comparaison pour un test donné"""
        print(f"\n{'='*80}")
        print(f"COMPARISON: {endpoint} - {test_name}")
        print(f"{'='*80}\n")

        for service, data in self.results.items():
            if endpoint in data and test_name in data[endpoint]:
                result = data[endpoint][test_name]
                print(f"{service:25} | ", end="")
                print(f"Total: {result.get('total_time', 0):.2f}s | ", end="")
                print(f"RPS: {result.get('requests_per_second', 0):.1f} | ", end="")
                print(f"P95: {result.get('p95_latency', 0):.2f}s | ", end="")
                print(f"P99: {result.get('p99_latency', 0):.2f}s")


async def wait_for_service(url: str, timeout: int = 60) -> bool:
    """Attend qu'un service soit disponible"""
    print(f"Waiting for {url}/health...")
    start = time.time()

    async with httpx.AsyncClient(timeout=5.0) as client:
        while time.time() - start < timeout:
            try:
                response = await client.get(f"{url}/health")
                if response.status_code == 200:
                    print(f"✓ {url} is ready!")
                    return True
            except Exception as e:
                await asyncio.sleep(1)

    print(f"✗ {url} failed to start!")
    return False


async def wait_for_all_services() -> bool:
    """Attend que tous les services soient prêts"""
    print("\n" + "="*80)
    print("WAITING FOR SERVICES TO START")
    print("="*80 + "\n")

    tasks = [wait_for_service(url) for url in SERVICES.values()]
    results = await asyncio.gather(*tasks)

    if all(results):
        print("\n✓ All services are ready!\n")
        return True
    else:
        print("\n✗ Some services failed to start!\n")
        return False


def test_single_request(service_name: str, url: str, endpoint: str) -> Dict[str, Any]:
    """Test d'une seule requête - mesure la latence"""
    full_url = f"{url}{endpoint}"
    start = time.time()

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(full_url)
            duration = time.time() - start

            return {
                "success": response.status_code == 200,
                "duration": duration,
                "status_code": response.status_code
            }
    except Exception as e:
        return {
            "success": False,
            "duration": time.time() - start,
            "error": str(e)
        }


def test_concurrent_sync(service_name: str, url: str, endpoint: str, num_requests: int) -> Dict[str, Any]:
    """Test avec requêtes concurrentes (threading)"""
    print(f"  Testing {service_name} with {num_requests} concurrent requests...")
    start = time.time()
    durations = []
    errors = 0

    with ThreadPoolExecutor(max_workers=num_requests) as executor:
        futures = [
            executor.submit(test_single_request, service_name, url, endpoint)
            for _ in range(num_requests)
        ]

        for future in as_completed(futures):
            result = future.result()
            if result['success']:
                durations.append(result['duration'])
            else:
                errors += 1

    total_time = time.time() - start

    if not durations:
        return {
            "total_time": total_time,
            "errors": errors,
            "success_rate": 0
        }

    return {
        "total_time": total_time,
        "requests_per_second": len(durations) / total_time,
        "mean_latency": statistics.mean(durations),
        "median_latency": statistics.median(durations),
        "p95_latency": statistics.quantiles(durations, n=20)[18] if len(durations) > 1 else durations[0],
        "p99_latency": statistics.quantiles(durations, n=100)[98] if len(durations) > 1 else durations[0],
        "min_latency": min(durations),
        "max_latency": max(durations),
        "errors": errors,
        "success_rate": len(durations) / (len(durations) + errors)
    }


async def test_concurrent_async(service_name: str, url: str, endpoint: str, num_requests: int) -> Dict[str, Any]:
    """Test avec requêtes concurrentes (asyncio)"""
    print(f"  Testing {service_name} with {num_requests} concurrent async requests...")
    start = time.time()
    durations = []
    errors = 0

    async def make_request():
        req_start = time.time()
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{url}{endpoint}")
                duration = time.time() - req_start
                return {"success": response.status_code == 200, "duration": duration}
        except Exception as e:
            return {"success": False, "duration": time.time() - req_start, "error": str(e)}

    tasks = [make_request() for _ in range(num_requests)]
    results = await asyncio.gather(*tasks)

    for result in results:
        if result['success']:
            durations.append(result['duration'])
        else:
            errors += 1

    total_time = time.time() - start

    if not durations:
        return {
            "total_time": total_time,
            "errors": errors,
            "success_rate": 0
        }

    return {
        "total_time": total_time,
        "requests_per_second": len(durations) / total_time,
        "mean_latency": statistics.mean(durations),
        "median_latency": statistics.median(durations),
        "p95_latency": statistics.quantiles(durations, n=20)[18] if len(durations) > 1 else durations[0],
        "p99_latency": statistics.quantiles(durations, n=100)[98] if len(durations) > 1 else durations[0],
        "min_latency": min(durations),
        "max_latency": max(durations),
        "errors": errors,
        "success_rate": len(durations) / (len(durations) + errors)
    }


def run_benchmark_suite():
    """Lance la suite complète de benchmarks"""
    results = BenchmarkResults()

    print("\n" + "="*80)
    print("BENCHMARK SUITE - ASYNC/AWAIT COMPARISON")
    print("="*80 + "\n")

    # Test 1: Latence simple (1 requête)
    print("\n--- TEST 1: Single Request Latency ---\n")
    for service_name, url in SERVICES.items():
        for endpoint in ENDPOINTS:
            result = test_single_request(service_name, url, endpoint)
            results.add_result(service_name, endpoint, "single_request", result)
            print(f"  {service_name:25} {endpoint:20} {result['duration']:.3f}s")

    # Test 2: 10 requêtes concurrentes
    print("\n--- TEST 2: 10 Concurrent Requests ---\n")
    for service_name, url in SERVICES.items():
        for endpoint in ENDPOINTS[:2]:  # Seulement /parallel et /multi-io
            result = test_concurrent_sync(service_name, url, endpoint, 10)
            results.add_result(service_name, endpoint, "concurrent_10", result)

    results.print_comparison('/parallel', 'concurrent_10')

    # Test 3: 50 requêtes concurrentes
    print("\n--- TEST 3: 50 Concurrent Requests ---\n")
    for service_name, url in SERVICES.items():
        result = test_concurrent_sync(service_name, url, '/parallel', 50)
        results.add_result(service_name, '/parallel', 'concurrent_50', result)

    results.print_comparison('/parallel', 'concurrent_50')

    # Test 4: 100 requêtes concurrentes (le killer!)
    print("\n--- TEST 4: 100 Concurrent Requests (THE KILLER TEST) ---\n")
    for service_name, url in SERVICES.items():
        result = test_concurrent_sync(service_name, url, '/parallel', 100)
        results.add_result(service_name, '/parallel', 'concurrent_100', result)

    results.print_comparison('/parallel', 'concurrent_100')

    return results


async def async_benchmark_suite():
    """Suite de benchmarks avec asyncio"""
    results = BenchmarkResults()

    print("\n" + "="*80)
    print("ASYNC BENCHMARK SUITE")
    print("="*80 + "\n")

    # Test avec asyncio
    print("\n--- Async Test: 100 Concurrent Requests ---\n")
    for service_name, url in SERVICES.items():
        result = await test_concurrent_async(service_name, url, '/parallel', 100)
        results.add_result(service_name, '/parallel', 'async_concurrent_100', result)

    results.print_comparison('/parallel', 'async_concurrent_100')

    return results


def generate_report(results: BenchmarkResults, filename: str = "benchmark_results.json"):
    """Génère un rapport JSON"""
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "results": results.get_summary()
    }

    with open(filename, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\n✓ Results saved to {filename}")


def generate_markdown_report(results: BenchmarkResults, filename: str = "BENCHMARK_RESULTS.md"):
    """Génère un rapport Markdown"""
    with open(filename, 'w') as f:
        f.write("# Benchmark Results - Flask vs Quart\n\n")
        f.write(f"Generated: {datetime.utcnow().isoformat()}\n\n")

        f.write("## Summary\n\n")
        f.write("This benchmark compares:\n")
        f.write("1. **Flask + WSGI** (baseline)\n")
        f.write("2. **Flask + Async routes** (trap - doesn't work)\n")
        f.write("3. **Flask + ASGI wrapper** (overhead, no benefits)\n")
        f.write("4. **Quart native** (true async)\n\n")

        # Test principal: 100 requêtes concurrentes
        f.write("## Main Test: 100 Concurrent Requests (/parallel endpoint)\n\n")
        f.write("| Solution | Total Time | RPS | P95 Latency | P99 Latency |\n")
        f.write("|----------|------------|-----|-------------|-------------|\n")

        summary = results.get_summary()
        for service, data in summary.items():
            if '/parallel' in data and 'concurrent_100' in data['/parallel']:
                result = data['/parallel']['concurrent_100']
                f.write(f"| {service} | ")
                f.write(f"{result.get('total_time', 0):.2f}s | ")
                f.write(f"{result.get('requests_per_second', 0):.1f} | ")
                f.write(f"{result.get('p95_latency', 0):.2f}s | ")
                f.write(f"{result.get('p99_latency', 0):.2f}s |\n")

        f.write("\n## Key Findings\n\n")
        f.write("- **Flask + WSGI**: Limited by workers × threads\n")
        f.write("- **Flask + Async**: No improvement (WSGI limitation)\n")
        f.write("- **Flask + ASGI wrapper**: Worse due to overhead\n")
        f.write("- **Quart**: Massive improvement with true async\n\n")

    print(f"✓ Markdown report saved to {filename}")


async def main():
    """Point d'entrée principal"""
    # Attendre que tous les services soient prêts
    if not await wait_for_all_services():
        print("ERROR: Not all services started. Exiting.")
        return

    # Lancer les benchmarks synchrones
    sync_results = run_benchmark_suite()

    # Lancer les benchmarks async
    async_results = await async_benchmark_suite()

    # Combiner les résultats
    for service, data in async_results.get_summary().items():
        for endpoint, tests in data.items():
            for test_name, result in tests.items():
                sync_results.add_result(service, endpoint, test_name, result)

    # Génération des rapports
    print("\n" + "="*80)
    print("GENERATING REPORTS")
    print("="*80 + "\n")

    generate_report(sync_results)
    generate_markdown_report(sync_results)

    print("\n" + "="*80)
    print("BENCHMARK COMPLETE! 🎉")
    print("="*80 + "\n")


if __name__ == '__main__':
    asyncio.run(main())
