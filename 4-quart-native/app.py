"""
Quart - Véritable framework ASGI async natif
Démontre la VRAIE puissance de async/await en Python
"""
import asyncio
import time
import os
import logging
from datetime import datetime
from quart import Quart, jsonify, websocket, request
import httpx

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Quart(__name__)

# Client HTTP async partagé
http_client = None

metrics = {
    "requests_total": 0,
    "requests_by_endpoint": {},
    "start_time": time.time(),
    "concurrent_requests_handled": 0
}


def track_request(endpoint_name):
    """Enregistre une requête dans les métriques"""
    metrics["requests_total"] += 1
    metrics["requests_by_endpoint"][endpoint_name] = \
        metrics["requests_by_endpoint"].get(endpoint_name, 0) + 1


@app.before_serving
async def startup():
    """Initialisation au démarrage"""
    global http_client
    http_client = httpx.AsyncClient(timeout=30.0)
    logger.info("✨ Quart app started with true async support!")


@app.after_serving
async def shutdown():
    """Nettoyage à l'arrêt"""
    global http_client
    if http_client:
        await http_client.aclose()
    logger.info("Quart app shut down cleanly")


@app.route('/health')
async def health():
    """Health check"""
    track_request('health')
    return jsonify({
        "status": "ok",
        "type": "quart-native-async",
        "worker_id": os.getpid(),
        "timestamp": datetime.utcnow().isoformat(),
        "feature": "TRUE async/await with ASGI! ✨"
    })


@app.route('/slow')
async def slow():
    """
    Opération I/O async - VRAIMENT non-bloquante!
    Le worker peut traiter d'autres requêtes pendant l'attente
    """
    track_request('slow')
    start = time.time()
    logger.info(f"[PID {os.getpid()}] /slow (QUART) - START - Worker remains free!")

    # await libère vraiment le worker ici!
    await asyncio.sleep(0.25)

    duration = time.time() - start
    logger.info(f"[PID {os.getpid()}] /slow (QUART) - END ({duration:.2f}s)")

    return jsonify({
        "message": "True async sleep - worker was free during wait!",
        "duration": duration,
        "timestamp": datetime.utcnow().isoformat(),
        "worker_id": os.getpid(),
        "benefit": "Other requests could be handled concurrently"
    })


@app.route('/multi-io')
async def multi_io():
    """
    Appels séquentiels async
    Chaque await libère le worker
    """
    track_request('multi-io')
    start = time.time()
    logger.info(f"[PID {os.getpid()}] /multi-io (QUART) - START")

    results = []
    for i in range(3):
        api_start = time.time()
        # Vraiment non-bloquant!
        await asyncio.sleep(0.125)
        api_duration = time.time() - api_start
        results.append({
            "call": i + 1,
            "duration": api_duration
        })
        logger.info(f"[PID {os.getpid()}] /multi-io (QUART) - Call {i+1}/3 done")

    total_duration = time.time() - start
    logger.info(f"[PID {os.getpid()}] /multi-io (QUART) - END ({total_duration:.2f}s)")

    return jsonify({
        "message": "3 sequential async calls - worker free between calls",
        "calls": results,
        "total_duration": total_duration,
        "worker_id": os.getpid(),
        "benefit": "Worker handled other requests during waits"
    })


@app.route('/parallel')
async def parallel():
    """
    LA MAGIE! Vraie exécution parallèle
    3 opérations I/O en même temps
    """
    track_request('parallel')
    start = time.time()
    logger.info(f"[PID {os.getpid()}] /parallel (QUART) - START")

    async def async_task(task_id, delay):
        """Tâche async"""
        logger.info(f"[PID {os.getpid()}] Task {task_id} starting...")
        await asyncio.sleep(delay)
        logger.info(f"[PID {os.getpid()}] Task {task_id} completed!")
        return {"task_id": task_id, "delay": delay}

    # Vraie exécution parallèle - ET le worker reste libre!
    results = await asyncio.gather(
        async_task(1, 0.5),
        async_task(2, 0.5),
        async_task(3, 0.5)
    )

    total_duration = time.time() - start
    metrics["concurrent_requests_handled"] += 3
    logger.info(f"[PID {os.getpid()}] /parallel (QUART) - END ({total_duration:.2f}s)")

    return jsonify({
        "message": "TRUE parallel execution with asyncio.gather!",
        "results": results,
        "total_duration": total_duration,
        "expected_duration": "~0.5s",
        "actual_speedup": f"{3 * 0.5 / total_duration:.1f}x faster than sequential",
        "worker_id": os.getpid(),
        "magic": "All 3 tasks ran concurrently! ✨"
    })


@app.route('/cpu-intensive')
async def cpu_intensive():
    """
    CPU intensive - async ne peut pas aider
    Mais on peut utiliser asyncio.to_thread pour ne pas bloquer
    """
    track_request('cpu-intensive')
    start = time.time()
    logger.info(f"[PID {os.getpid()}] /cpu-intensive (QUART) - START")

    # Pour du CPU-bound, il faut utiliser un thread pool
    def cpu_work():
        return sum(range(10_000_000))

    # Exécute dans un thread séparé pour ne pas bloquer l'event loop
    result = await asyncio.to_thread(cpu_work)

    duration = time.time() - start
    logger.info(f"[PID {os.getpid()}] /cpu-intensive (QUART) - END ({duration:.2f}s)")

    return jsonify({
        "message": "CPU intensive work offloaded to thread pool",
        "result": result,
        "duration": duration,
        "worker_id": os.getpid(),
        "note": "Used asyncio.to_thread to avoid blocking event loop"
    })


@app.route('/db-simulation')
async def db_simulation():
    """DB simulation - vraiment async"""
    track_request('db-simulation')
    start = time.time()
    logger.info(f"[PID {os.getpid()}] /db-simulation (QUART) - START")

    # Simule une requête DB async
    await asyncio.sleep(0.075)

    duration = time.time() - start
    logger.info(f"[PID {os.getpid()}] /db-simulation (QUART) - END ({duration:.2f}s)")

    return jsonify({
        "message": "Async DB query simulation",
        "rows_affected": 42,
        "duration": duration,
        "worker_id": os.getpid(),
        "benefit": "Worker was free during DB query"
    })


@app.route('/external-api')
async def external_api():
    """
    Vraie requête HTTP async avec httpx
    Démontre l'I/O non-bloquant réel
    """
    track_request('external-api')
    start = time.time()
    logger.info(f"[PID {os.getpid()}] /external-api (QUART) - START")

    try:
        # Requête HTTP vraiment async
        response = await http_client.get('https://httpbin.org/delay/1')
        data = response.json()

        duration = time.time() - start
        logger.info(f"[PID {os.getpid()}] /external-api (QUART) - END ({duration:.2f}s)")

        return jsonify({
            "message": "True async HTTP request completed",
            "duration": duration,
            "response_status": response.status_code,
            "worker_id": os.getpid(),
            "benefit": "Worker handled other requests during HTTP call"
        })
    except Exception as e:
        logger.error(f"External API error: {e}")
        return jsonify({
            "error": str(e),
            "duration": time.time() - start
        }), 500


@app.route('/metrics')
async def get_metrics():
    """Métriques de l'application"""
    uptime = time.time() - metrics["start_time"]
    return jsonify({
        "type": "quart-native-async",
        "worker_id": os.getpid(),
        "uptime_seconds": uptime,
        "requests_total": metrics["requests_total"],
        "requests_by_endpoint": metrics["requests_by_endpoint"],
        "requests_per_second": metrics["requests_total"] / uptime if uptime > 0 else 0,
        "concurrent_requests_handled": metrics["concurrent_requests_handled"],
        "feature": "True async with ASGI! ✨"
    })


@app.websocket('/ws')
async def ws():
    """
    WebSocket endpoint - seulement possible avec ASGI!
    Connexion bidirectionnelle en temps réel
    """
    logger.info(f"[PID {os.getpid()}] WebSocket connection established")
    try:
        while True:
            data = await websocket.receive()
            logger.info(f"[PID {os.getpid()}] WS received: {data}")
            await websocket.send(f"Echo: {data}")
    except asyncio.CancelledError:
        logger.info(f"[PID {os.getpid()}] WebSocket connection closed")
        raise


@app.route('/sse')
async def sse():
    """
    Server-Sent Events - streaming en temps réel
    Seulement possible avec ASGI!
    """
    track_request('sse')

    async def generate():
        """Génère des événements en temps réel"""
        for i in range(10):
            await asyncio.sleep(0.125)
            yield f"data: Event {i} at {datetime.utcnow().isoformat()}\n\n"

    return generate(), {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'X-Accel-Buffering': 'no'
    }


@app.errorhandler(Exception)
async def handle_error(e):
    """Gestionnaire d'erreurs global"""
    logger.error(f"Error: {str(e)}", exc_info=True)
    return jsonify({
        "error": str(e),
        "type": "quart-native-async"
    }), 500


if __name__ == '__main__':
    logger.info("✨ Starting Quart with TRUE async support!")
    logger.info("✨ Use: uvicorn app:app --host 0.0.0.0 --port 5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
