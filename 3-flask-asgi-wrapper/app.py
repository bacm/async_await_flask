"""
Flask + ASGI Wrapper avec async/await
Utilise asgiref pour wrapper Flask WSGI en ASGI
Fonctionne mais avec overhead comparé à Quart natif
"""
import asyncio
import time
import os
import logging
from datetime import datetime
from flask import Flask, jsonify
from asgiref.wsgi import WsgiToAsgi

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Flask app classique
flask_app = Flask(__name__)

metrics = {
    "requests_total": 0,
    "requests_by_endpoint": {},
    "start_time": time.time(),
    "wrapper_overhead_ms": []
}


def track_request(endpoint_name, overhead_ms=0):
    """Enregistre une requête dans les métriques"""
    metrics["requests_total"] += 1
    metrics["requests_by_endpoint"][endpoint_name] = \
        metrics["requests_by_endpoint"].get(endpoint_name, 0) + 1
    if overhead_ms > 0:
        metrics["wrapper_overhead_ms"].append(overhead_ms)


@flask_app.route('/health')
async def health():
    """Health check"""
    track_request('health')
    return jsonify({
        "status": "ok",
        "type": "flask-asgi-wrapper",
        "worker_id": os.getpid(),
        "timestamp": datetime.utcnow().isoformat(),
        "note": "Flask with async/await on ASGI - works but has overhead"
    })


@flask_app.route('/slow')
async def slow():
    """
    Async/await sur ASGI wrapper
    Fonctionne mais avec overhead comparé à Quart
    """
    track_request('slow')
    start = time.time()
    logger.info(f"[PID {os.getpid()}] /slow (ASGI wrapper) - START")

    # await asyncio.sleep fonctionne sur ASGI
    await asyncio.sleep(0.25)

    duration = time.time() - start
    logger.info(f"[PID {os.getpid()}] /slow (ASGI wrapper) - END ({duration:.2f}s)")

    return jsonify({
        "message": "Flask async on ASGI wrapper - works but has overhead",
        "duration": duration,
        "timestamp": datetime.utcnow().isoformat(),
        "worker_id": os.getpid(),
        "note": "Functional but slower than Quart native"
    })


@flask_app.route('/multi-io')
async def multi_io():
    """
    Appels séquentiels - toujours bloquants
    Le wrapper ASGI ajoute juste de l'overhead
    """
    track_request('multi-io')
    start = time.time()
    logger.info(f"[PID {os.getpid()}] /multi-io (ASGI wrapper) - START")

    results = []
    for i in range(3):
        api_start = time.time()
        await asyncio.sleep(0.125)
        api_duration = time.time() - api_start
        results.append({
            "call": i + 1,
            "duration": api_duration
        })
        logger.info(f"[PID {os.getpid()}] /multi-io (ASGI wrapper) - Call {i+1}/3 done")

    total_duration = time.time() - start
    logger.info(f"[PID {os.getpid()}] /multi-io (ASGI wrapper) - END ({total_duration:.2f}s)")

    return jsonify({
        "message": "Sequential calls with ASGI wrapper overhead",
        "calls": results,
        "total_duration": total_duration,
        "worker_id": os.getpid(),
        "problem": "Wrapper adds overhead, Flask underneath is still synchronous"
    })


@flask_app.route('/cpu-intensive')
async def cpu_intensive():
    """CPU intensive - wrapper inutile"""
    track_request('cpu-intensive')
    start = time.time()
    logger.info(f"[PID {os.getpid()}] /cpu-intensive (ASGI wrapper) - START")

    result = sum(range(10_000_000))

    duration = time.time() - start
    logger.info(f"[PID {os.getpid()}] /cpu-intensive (ASGI wrapper) - END ({duration:.2f}s)")

    return jsonify({
        "message": "CPU intensive with ASGI wrapper (useless overhead)",
        "result": result,
        "duration": duration,
        "worker_id": os.getpid()
    })


@flask_app.route('/db-simulation')
async def db_simulation():
    """DB simulation - wrapper n'aide pas"""
    track_request('db-simulation')
    start = time.time()
    logger.info(f"[PID {os.getpid()}] /db-simulation (ASGI wrapper) - START")

    await asyncio.sleep(0.075)

    duration = time.time() - start
    logger.info(f"[PID {os.getpid()}] /db-simulation (ASGI wrapper) - END ({duration:.2f}s)")

    return jsonify({
        "message": "DB simulation with ASGI wrapper",
        "rows_affected": 42,
        "duration": duration,
        "worker_id": os.getpid(),
        "note": "Wrapper overhead with no async benefits"
    })


@flask_app.route('/metrics')
async def get_metrics():
    """Métriques avec overhead du wrapper"""
    uptime = time.time() - metrics["start_time"]
    avg_overhead = sum(metrics["wrapper_overhead_ms"]) / len(metrics["wrapper_overhead_ms"]) \
        if metrics["wrapper_overhead_ms"] else 0

    return jsonify({
        "type": "flask-asgi-wrapper",
        "worker_id": os.getpid(),
        "uptime_seconds": uptime,
        "requests_total": metrics["requests_total"],
        "requests_by_endpoint": metrics["requests_by_endpoint"],
        "requests_per_second": metrics["requests_total"] / uptime if uptime > 0 else 0,
        "average_wrapper_overhead_ms": avg_overhead,
        "warning": "ASGI wrapper adds overhead without async benefits!",
        "recommendation": "Use Quart instead!"
    })


@flask_app.errorhandler(Exception)
def handle_error(e):
    """Gestionnaire d'erreurs global"""
    logger.error(f"Error: {str(e)}", exc_info=True)
    return jsonify({
        "error": str(e),
        "type": "flask-asgi-wrapper"
    }), 500


# Wrapper WSGI → ASGI
# Ajoute de l'overhead sans bénéfices
logger.warning("⚠️  Wrapping Flask (WSGI) with ASGI adapter")
logger.warning("⚠️  This adds overhead without providing async benefits!")
logger.warning("⚠️  Flask underneath is still synchronous!")
logger.warning("⚠️  WsgiToAsgi has poor concurrency handling - requests are mostly sequential!")

# WsgiToAsgi wrapper - configuration limitée
# Le thread pool est géré par asgiref mais pas optimisé pour haute concurrence
asgi_app = WsgiToAsgi(flask_app)


if __name__ == '__main__':
    logger.error("❌ Cannot run ASGI app with flask dev server!")
    logger.info("Use: hypercorn app:asgi_app --bind 0.0.0.0:5000")

@flask_app.route('/parallel')
async def parallel():
    """
    2 opérations EN PARALLÈLE avec asyncio.gather
    Démontre l'avantage de l'async!
    """
    track_request('parallel')
    start = time.time()
    logger.info(f"[PID {os.getpid()}] /parallel (ASGI) - START")

    await asyncio.gather(
        asyncio.sleep(0.25),
        asyncio.sleep(0.25)
    )

    duration = time.time() - start
    logger.info(f"[PID {os.getpid()}] /parallel (ASGI) - END ({duration:.2f}s)")

    return jsonify({
        "message": "ASGI: Parallel execution with asyncio.gather",
        "duration": duration,
        "expected": "~0.25s (2 × 0.25s in parallel)",
        "worker_id": os.getpid(),
        "note": "2x faster than sequential!"
    })
