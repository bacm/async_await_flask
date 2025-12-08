"""
Flask WSGI - Baseline synchronous application
Demonstrates traditional Flask with WSGI (Gunicorn)
"""
import time
import os
import logging
from datetime import datetime
from flask import Flask, jsonify, request

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Métriques globales
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
def health():
    """Health check endpoint"""
    track_request('health')
    return jsonify({
        "status": "ok",
        "type": "flask-wsgi",
        "worker_id": os.getpid(),
        "timestamp": datetime.utcnow().isoformat()
    })


@app.route('/slow')
def slow():
    """Simule une opération I/O bloquante (1 seconde)"""
    track_request('slow')
    start = time.time()
    logger.info(f"[PID {os.getpid()}] /slow - START")

    # I/O bloquant - bloque le thread entier
    time.sleep(0.25)

    duration = time.time() - start
    logger.info(f"[PID {os.getpid()}] /slow - END ({duration:.2f}s)")

    return jsonify({
        "message": "Completed after 250ms (blocking sleep)",
        "duration": duration,
        "timestamp": datetime.utcnow().isoformat(),
        "worker_id": os.getpid()
    })


@app.route('/multi-io')
def multi_io():
    """Simule 3 appels API séquentiels (0.5s chacun)"""
    track_request('multi-io')
    start = time.time()
    logger.info(f"[PID {os.getpid()}] /multi-io - START")

    results = []
    for i in range(3):
        api_start = time.time()
        # Simule un appel API externe
        time.sleep(0.125)
        api_duration = time.time() - api_start
        results.append({
            "call": i + 1,
            "duration": api_duration
        })
        logger.info(f"[PID {os.getpid()}] /multi-io - Call {i+1}/3 done")

    total_duration = time.time() - start
    logger.info(f"[PID {os.getpid()}] /multi-io - END ({total_duration:.2f}s)")

    return jsonify({
        "message": "3 sequential API calls completed",
        "calls": results,
        "total_duration": total_duration,
        "worker_id": os.getpid()
    })


@app.route('/parallel')
def parallel():
    """
    2 opérations séquentielles - WSGI ne peut pas paralléliser
    Démontre pourquoi async est important
    """
    track_request('parallel')
    start = time.time()
    logger.info(f"[PID {os.getpid()}] /parallel - START")

    # WSGI: Must do sequentially - 0.25s + 0.25s = 0.5s
    time.sleep(0.25)
    time.sleep(0.25)

    duration = time.time() - start
    logger.info(f"[PID {os.getpid()}] /parallel - END ({duration:.2f}s)")

    return jsonify({
        "message": "WSGI: Sequential execution (no parallelization possible)",
        "duration": duration,
        "expected": "~0.5s (2 × 0.25s)",
        "worker_id": os.getpid()
    })


@app.route('/cpu-intensive')
def cpu_intensive():
    """Opération CPU intensive"""
    track_request('cpu-intensive')
    start = time.time()
    logger.info(f"[PID {os.getpid()}] /cpu-intensive - START")

    # Calcul CPU lourd
    result = sum(range(10_000_000))

    duration = time.time() - start
    logger.info(f"[PID {os.getpid()}] /cpu-intensive - END ({duration:.2f}s)")

    return jsonify({
        "message": "CPU intensive calculation completed",
        "result": result,
        "duration": duration,
        "worker_id": os.getpid()
    })


@app.route('/db-simulation')
def db_simulation():
    """Simule une requête de base de données"""
    track_request('db-simulation')
    start = time.time()
    logger.info(f"[PID {os.getpid()}] /db-simulation - START")

    # Simule latence DB
    time.sleep(0.075)

    duration = time.time() - start
    logger.info(f"[PID {os.getpid()}] /db-simulation - END ({duration:.2f}s)")

    return jsonify({
        "message": "Database query simulation completed",
        "rows_affected": 42,
        "duration": duration,
        "worker_id": os.getpid()
    })


@app.route('/metrics')
def get_metrics():
    """Retourne les métriques de l'application"""
    uptime = time.time() - metrics["start_time"]
    return jsonify({
        "type": "flask-wsgi",
        "worker_id": os.getpid(),
        "uptime_seconds": uptime,
        "requests_total": metrics["requests_total"],
        "requests_by_endpoint": metrics["requests_by_endpoint"],
        "requests_per_second": metrics["requests_total"] / uptime if uptime > 0 else 0
    })


@app.errorhandler(Exception)
def handle_error(e):
    """Gestionnaire d'erreurs global"""
    logger.error(f"Error: {str(e)}", exc_info=True)
    return jsonify({
        "error": str(e),
        "type": "flask-wsgi"
    }), 500


if __name__ == '__main__':
    # Development only - en production on utilise Gunicorn
    logger.info("Starting Flask WSGI app in development mode")
    app.run(host='0.0.0.0', port=5000, debug=True)
