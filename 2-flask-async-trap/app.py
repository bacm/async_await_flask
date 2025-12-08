"""
Flask avec routes async - Le PIÈGE!
Démontre que async/await dans Flask + WSGI ne fonctionne PAS comme attendu
Les routes sont async mais tournent sur WSGI donc pas de vrai concurrence
"""
import asyncio
import time
import os
import logging
from datetime import datetime
from flask import Flask, jsonify

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

metrics = {
    "requests_total": 0,
    "requests_by_endpoint": {},
    "start_time": time.time()
}


def track_request(endpoint_name):
    """Enregistre une requête dans les métriques"""
    metrics["requests_total"] += 1
    metrics["requests_by_endpoint"][endpoint_name] = \
        metrics["requests_by_endpoint"].get(endpoint_name, 0) + 1


@app.route('/health')
async def health():
    """Health check - async mais ça ne change rien sous WSGI"""
    track_request('health')
    return jsonify({
        "status": "ok",
        "type": "flask-async-trap",
        "worker_id": os.getpid(),
        "timestamp": datetime.utcnow().isoformat(),
        "warning": "This is async but runs on WSGI - NO real concurrency!"
    })


@app.route('/slow')
async def slow():
    """
    Route async avec asyncio.sleep
    ATTENTION: Sous WSGI, ça ne libère PAS le thread!
    """
    track_request('slow')
    start = time.time()
    logger.info(f"[PID {os.getpid()}] /slow (async) - START")

    # asyncio.sleep mais sur WSGI = toujours bloquant au niveau du worker
    await asyncio.sleep(0.25)

    duration = time.time() - start
    logger.info(f"[PID {os.getpid()}] /slow (async) - END ({duration:.2f}s)")

    return jsonify({
        "message": "async/await used but still blocks WSGI worker!",
        "duration": duration,
        "timestamp": datetime.utcnow().isoformat(),
        "worker_id": os.getpid(),
        "reality_check": "This does NOT help with concurrency on WSGI"
    })


@app.route('/multi-io')
async def multi_io():
    """
    Tentative d'appels séquentiels avec async
    Toujours séquentiel sous WSGI
    """
    track_request('multi-io')
    start = time.time()
    logger.info(f"[PID {os.getpid()}] /multi-io (async) - START")

    results = []
    for i in range(3):
        api_start = time.time()
        await asyncio.sleep(0.125)
        api_duration = time.time() - api_start
        results.append({
            "call": i + 1,
            "duration": api_duration
        })
        logger.info(f"[PID {os.getpid()}] /multi-io (async) - Call {i+1}/3 done")

    total_duration = time.time() - start
    logger.info(f"[PID {os.getpid()}] /multi-io (async) - END ({total_duration:.2f}s)")

    return jsonify({
        "message": "Sequential async calls - but WSGI doesn't care!",
        "calls": results,
        "total_duration": total_duration,
        "worker_id": os.getpid(),
        "note": "Still takes ~1.5s because WSGI is synchronous"
    })


@app.route('/parallel-attempt')
async def parallel_attempt():
    """
    LE PIÈGE DÉMONTRÉ!
    Tentative d'exécution parallèle avec asyncio.gather
    Ça SEMBLE marcher mais c'est trompeur - le worker reste bloqué
    """
    track_request('parallel-attempt')
    start = time.time()
    logger.info(f"[PID {os.getpid()}] /parallel-attempt - START")
    logger.warning("⚠️  TRAP: asyncio.gather works but worker is STILL blocked!")

    async def fake_api_call(call_id, delay):
        """Simule un appel API"""
        logger.info(f"[PID {os.getpid()}] Call {call_id} starting...")
        await asyncio.sleep(delay)
        logger.info(f"[PID {os.getpid()}] Call {call_id} done")
        return {"call_id": call_id, "delay": delay}

    # Ça va s'exécuter en "parallèle" dans l'event loop
    # MAIS le worker WSGI reste bloqué pendant tout ce temps!
    results = await asyncio.gather(
        fake_api_call(1, 0.5),
        fake_api_call(2, 0.5),
        fake_api_call(3, 0.5)
    )

    total_duration = time.time() - start
    logger.info(f"[PID {os.getpid()}] /parallel-attempt - END ({total_duration:.2f}s)")
    logger.warning(f"⚠️  Took {total_duration:.2f}s - WSGI worker was blocked the whole time!")

    return jsonify({
        "message": "asyncio.gather completed",
        "results": results,
        "total_duration": total_duration,
        "expected_if_parallel": "~0.5s",
        "actual_duration": f"{total_duration:.2f}s",
        "reality_check": "Takes ~0.5s but WSGI worker is blocked - other requests wait!",
        "explanation": "The async code runs but the WSGI worker thread is blocked waiting for it",
        "problem": "No other request can be handled by this worker during this time",
        "worker_id": os.getpid()
    })


@app.route('/cpu-intensive')
async def cpu_intensive():
    """CPU intensive - async ne change RIEN ici"""
    track_request('cpu-intensive')
    start = time.time()
    logger.info(f"[PID {os.getpid()}] /cpu-intensive (async) - START")

    # Calcul CPU - async ne peut pas aider ici de toute façon
    result = sum(range(10_000_000))

    duration = time.time() - start
    logger.info(f"[PID {os.getpid()}] /cpu-intensive (async) - END ({duration:.2f}s)")

    return jsonify({
        "message": "CPU intensive with async keyword (pointless)",
        "result": result,
        "duration": duration,
        "worker_id": os.getpid(),
        "note": "async/await can't help with CPU-bound tasks anyway"
    })


@app.route('/db-simulation')
async def db_simulation():
    """DB simulation - async sous WSGI = illusion"""
    track_request('db-simulation')
    start = time.time()
    logger.info(f"[PID {os.getpid()}] /db-simulation (async) - START")

    await asyncio.sleep(0.075)

    duration = time.time() - start
    logger.info(f"[PID {os.getpid()}] /db-simulation (async) - END ({duration:.2f}s)")

    return jsonify({
        "message": "async DB simulation on WSGI",
        "rows_affected": 42,
        "duration": duration,
        "worker_id": os.getpid(),
        "trap": "await doesn't free the WSGI worker!"
    })


@app.route('/metrics')
async def get_metrics():
    """Métriques"""
    uptime = time.time() - metrics["start_time"]
    return jsonify({
        "type": "flask-async-trap",
        "worker_id": os.getpid(),
        "uptime_seconds": uptime,
        "requests_total": metrics["requests_total"],
        "requests_by_endpoint": metrics["requests_by_endpoint"],
        "requests_per_second": metrics["requests_total"] / uptime if uptime > 0 else 0,
        "warning": "These async routes don't provide concurrency on WSGI!"
    })


@app.errorhandler(Exception)
def handle_error(e):
    """Gestionnaire d'erreurs global"""
    logger.error(f"Error: {str(e)}", exc_info=True)
    return jsonify({
        "error": str(e),
        "type": "flask-async-trap"
    }), 500


if __name__ == '__main__':
    logger.warning("⚠️  Running Flask with async routes on WSGI - THIS IS A TRAP!")
    logger.warning("⚠️  async/await syntax works but provides NO concurrency benefits!")
    logger.warning("⚠️  Use Quart or FastAPI for true async behavior!")
    app.run(host='0.0.0.0', port=5000, debug=True)
