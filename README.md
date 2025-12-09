# Flask vs Quart: Async/Await Démonstration

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-3.0.0-green.svg)](https://flask.palletsprojects.com/)
[![Quart](https://img.shields.io/badge/Quart-0.19.4-blue.svg)](https://quart.palletsprojects.com/)
[![Docker](https://img.shields.io/badge/Docker-ready-blue.svg)](https://www.docker.com/)

**Projet de démonstration complet** pour comprendre les différences entre Flask (WSGI), Flask avec async, Flask+ASGI wrapper, et Quart (ASGI natif).

## 📋 Table des matières

- [Le Problème](#-le-problème)
- [Les Solutions Comparées](#-les-solutions-comparées)
- [Structure du Projet](#-structure-du-projet)
- [Installation et Utilisation](#-installation-et-utilisation)
- [Résultats Attendus](#-résultats-attendus)
- [Explications Détaillées](#-explications-détaillées)

---

## 🎯 Le Problème

En Python, `async/await` permet de gérer des opérations I/O de manière non-bloquante. Cependant, **tous les frameworks web ne supportent pas vraiment async**.

### Pourquoi c'est important?

Imaginez une application qui fait des appels à une API externe:

```python
# Synchrone (bloquant)
def handle_request():
    result1 = call_api()  # Attend 1s - BLOQUE le thread
    result2 = call_api()  # Attend 1s - BLOQUE le thread
    result3 = call_api()  # Attend 1s - BLOQUE le thread
    return result1 + result2 + result3
    # Total: 3 secondes, aucune autre requête ne peut être traitée
```

```python
# Async (non-bloquant)
async def handle_request():
    results = await asyncio.gather(
        call_api(),  # Les 3 s'exécutent
        call_api(),  # en parallèle!
        call_api()
    )
    return sum(results)
    # Total: 1 seconde, le worker reste libre pour traiter d'autres requêtes
```

#### Comparaison Visuelle avec 1 worker
Avec un IO de 300 secs, et 2 requêtes simultanées
```
SYNCHRONE (Flask)
═════════════════
Requête 1: [████████████] 500ms          
                          Requête 2: [████████████] 500ms          
           └──────────────────────────────────────┘
                             Total: 1000ms


ASYNCHRONE (Quart) avec I/O non bloquants
══════════════════════════════════════════
Requête 1: [██ CPU ██][...... I/O async ......][██ CPU ██]   500ms total
Requête 2:            [██ CPU ██][...... I/O async ......][██ CPU ██]   600ms total
                      │              │
           └─ 100 ms ─└────── SUPERPOSITION DES I/O ─────┘└ 100 ms ─┘

                       Temps total du serveur : 600ms
```

---

## 🔍 Les Solutions Comparées

### 1️⃣ Flask + WSGI (Baseline)

**Le standard synchrone classique**

```python
from flask import Flask

app = Flask(__name__)

@app.route('/parallel')
def parallel():
    time.sleep(0.25)  # BLOQUE le worker
    time.sleep(0.25)  # BLOQUE le worker
    return {"status": "done"}
```

**Caractéristiques:**
- ✅ Stable, mature, bien compris
- ✅ Parfait pour des applications CPU-bound
- ❌ Limité par `workers × threads` si utilisation de gthread sinon limité par `workers`
- ❌ Chaque requête bloque un thread

**Configuration typique:** Gunicorn avec 2 workers × 2 threads = **4 requêtes maximum en parallèle**

---

### 2️⃣ Flask + Async Routes (LE PIÈGE!)

**Flask 3.0+ supporte les routes async, MAIS...**

```python
from flask import Flask

app = Flask(__name__)

@app.route('/parallel')
async def parallel():
    await asyncio.sleep(0.25)  # Async MAIS...
    await asyncio.sleep(0.25)  # Async MAIS...
    return {"status": "done"}
```

**Le problème:**
- ⚠️ Flask tourne toujours sur WSGI
- ⚠️ `async def` fonctionne mais ne libère PAS le worker
- ⚠️ Aucun gain de performance

**Verdict:** 🚫 **C'EST UN PIÈGE!** N'utilisez pas async avec WSGI.

---

### 3️⃣ Flask + ASGI Wrapper (MAUVAISE IDÉE)

**Utiliser `asgiref` pour wrapper Flask:**

```python
from flask import Flask
from asgiref.wsgi import WsgiToAsgi

app = Flask(__name__)
asgi_app = WsgiToAsgi(app)  # Wrapper WSGI → ASGI
```

**Le problème:**
- ⚠️ Ajoute de l'overhead de conversion
- ⚠️ Flask reste synchrone en dessous
- ⚠️ Aucun bénéfice de async

**Verdict:** 🚫 ça semble le pire des 2 mondes

---

### 4️⃣ Quart (LA BONNE SOLUTION! ✨)

**Framework ASGI natif, API compatible Flask:**

```python
from quart import Quart

app = Quart(__name__)

@app.route('/parallel')
async def parallel():
    await asyncio.gather(
        asyncio.sleep(0.25),
        asyncio.sleep(0.25)
    )  # Libère VRAIMENT le worker!
    return {"status": "done"}
```

**Les avantages:**
- ✅ Véritable async/await
- ✅ Un seul worker peut gérer des centaines de requêtes concurrentes
- ✅ API quasi-identique à Flask (migration facile)
- ✅ Support WebSocket et Server-Sent Events
- ✅ Performance exceptionnelle pour I/O-bound

**Verdict:** ✅ **LA SOLUTION!** Pour des applications I/O-bound.

---

## 📁 Structure du Projet

```
async-await-demo/
├── 1-flask-wsgi/              # Flask classique (baseline)
│   ├── app.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── 2-flask-async-trap/        # Flask + async (piège!)
│   ├── app.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── 3-flask-asgi-wrapper/      # Flask + wrapper ASGI (mauvais)
│   ├── app.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── 4-quart-native/            # Quart natif (solution!)
│   ├── app.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── benchmarks/                # Suite de benchmarks
│   ├── test_all.py           # Tests de performance
│   ├── visual_benchmark.py   # Génération de graphiques
│   ├── requirements.txt
│   └── Dockerfile
│
├── docker-compose.global.yml  # Lance tous les services
├── Makefile                   # Commandes utiles
├── setup.sh                   # Installation locale
├── presentation.py            # Présentation interactive
├── .env.example              # Variables d'environnement
└── README.md                 # Ce fichier
```

---

## 🚀 Installation et Utilisation

### Prérequis

- Docker & Docker Compose
- Make (optionnel mais recommandé)
- Python 3.11+ (pour tests locaux)

### Démarrage Rapide

```bash
# 1. Cloner le repo
git clone <repo-url>
cd async-await-demo

# 2. Build tous les containers
make build

# 3. Lancer tous les services
make up

# 4. Vérifier que tout fonctionne
make health

# 5. Lancer une démo interactive
make demo

# 6. Lancer les benchmarks complets
make report
```

### Services Disponibles

Une fois lancés, les services sont accessibles sur:

- **Flask WSGI:** http://localhost:5001
- **Flask Async Trap:** http://localhost:5002
- **Flask ASGI Wrapper:** http://localhost:5003
- **Quart Native:** http://localhost:5004

### Endpoints Disponibles

Chaque service expose les mêmes endpoints:

| Endpoint | Description |
|----------|-------------|
| `/health` | Health check |
| `/parallel` | 2 opérations I/O de 0.25s |
| `/multi-io` | 3 appels séquentiels de 0.5s |
| `/cpu-intensive` | Calcul CPU lourd |
| `/db-simulation` | Simulation de requête DB (0.3s) |
| `/metrics` | Statistiques du service |

**Quart uniquement:**
- `/slow` - Opération I/O de 0.25s
- `/sse` - Server-Sent Events
- `/ws` - WebSocket

### Commandes Make Disponibles

```bash
make help              # Affiche toutes les commandes
make build             # Build les containers
make up                # Lance tous les services
make down              # Arrête tous les services
make logs              # Affiche les logs
make status            # Status des services
make health            # Health check
make test              # Lance les benchmarks
make visual            # Génère les graphiques
make report            # Test + visualisations
make demo              # Démo interactive
make clean             # Nettoie tout
```

---

## 📊 Résultats Attendus

### Test: 100 Requêtes Concurrentes (/parallel endpoint)

Chaque requête fait deux `sleep(0.25)` (simule des appels API parallèles).

| Solution | Temps Total | RPS | P95 Latency | Verdict |
|----------|-------------|-----|-------------|---------|
| **Flask WSGI** | ~25s | 4.0 | ~24s | ⚠️ Limité à 4 workers |
| **Flask Async** | ~26s | 3.8 | ~25s | 🚫 **PIRE** que sync! |
| **Flask + ASGI** | ~29s | 3.4 | ~28s | 🚫 **LE PIRE** (overhead) |
| **Quart Native** | ~1.2s | 83.3 | ~1.1s | ✅ **21x plus rapide!** |

### Pourquoi Cette Différence?

**Flask WSGI (2 workers, 2 threads = 4 max):**
```
Worker 1 Thread 1: [==============] 25s
Worker 1 Thread 2: [==============] 25s  } Traite 4 requêtes
Worker 2 Thread 1: [==============] 25s  } puis attend
Worker 2 Thread 2: [==============] 25s  } les 96 autres...

Total: 100 requêtes / 4 slots = 25 rounds × 1s = 25 secondes
```

**Quart (1 worker async):**
```
Worker Async: [100 requêtes en parallèle!] 1s

Total: Toutes les requêtes en même temps = 1 seconde
```

---

## 📚 Explications Détaillées

### Pourquoi Flask + Async Ne Fonctionne Pas?

Flask 3.0+ supporte la syntaxe `async def`, mais cela ne change rien au niveau de la concurrence car:

1. **WSGI est fondamentalement synchrone**
   - Un worker = un processus
   - Un thread par requête
   - `await` s'exécute mais bloque le thread

2. **L'event loop est créé par requête**
   - Chaque requête async a sa propre event loop
   - Pas de partage de l'event loop entre requêtes
   - Aucune concurrence réelle

3. **Overhead sans bénéfices**
   - Création/destruction d'event loop par requête
   - Plus lent que du code synchrone pur

### Pourquoi le Wrapper ASGI Est Mauvais?

`WsgiToAsgi` convertit une app WSGI en ASGI, mais:

1. **Overhead de conversion**
   - Conversion request ASGI → WSGI
   - Conversion response WSGI → ASGI
   - Coût CPU supplémentaire

2. **Flask reste synchrone**
   - Le code Flask s'exécute toujours de manière synchrone
   - Aucun bénéfice de async

3. **Pire des deux mondes**
   - Complexité de ASGI
   - Performance de WSGI
   - Overhead en plus

### Comment Quart Fonctionne?

Quart est construit sur ASGI dès le début:

1. **Event loop partagé**
   - Un seul event loop par worker
   - Toutes les requêtes partagent l'event loop
   - Véritable concurrence

2. **async/await natif**
   - `await` libère vraiment le worker
   - D'autres requêtes peuvent s'exécuter
   - Pas d'overhead inutile

3. **Architecture moderne**
   - Support WebSocket natif
   - Server-Sent Events
   - HTTP/2 ready

---

## 🎓 Quand Utiliser Quoi?

### Utilisez Flask (WSGI) si:

- ✅ Application majoritairement CPU-bound
- ✅ Peu d'opérations I/O externes
- ✅ Équipe pas familière avec async
- ✅ Utilisation d'extensions Flask spécifiques

### Utilisez Quart (ASGI) si:

- ✅ Beaucoup d'appels API externes
- ✅ Requêtes base de données fréquentes
- ✅ Besoin de WebSocket ou SSE
- ✅ Charge haute avec peu de ressources
- ✅ Opérations I/O bound

### N'utilisez JAMAIS:

- 🚫 Flask avec routes async sur WSGI
- 🚫 Flask wrappé avec WsgiToAsgi
- 🚫 async pour du code CPU-bound

---

## 🧪 Détails des Benchmarks

### Méthodologie

Les benchmarks testent:

1. **Latence simple** - 1 requête pour mesurer l'overhead
2. **10 requêtes concurrentes** - Charge légère
3. **50 requêtes concurrentes** - Charge moyenne
4. **100 requêtes concurrentes** - Charge haute (le killer!)

### Métriques Collectées

- **Total Time:** Temps pour traiter toutes les requêtes
- **RPS:** Requêtes par seconde (throughput)
- **P50 (médiane):** 50% des requêtes plus rapides que ça
- **P95:** 95% des requêtes plus rapides que ça
- **P99:** 99% des requêtes plus rapides que ça

### Endpoints Testés

- `/parallel` - 2×0.25s sleep (I/O parallèle ou séquentiel)
- `/multi-io` - 3×0.5s sleep séquentiel
- `/cpu-intensive` - Calcul CPU lourd
- `/db-simulation` - Simule une requête DB

---

## 🔧 Configuration et Personnalisation

### Variables d'Environnement

Créez un fichier `.env`:

```bash
# Flask WSGI
FLASK_WSGI_WORKERS=2
FLASK_WSGI_THREADS=2

# Quart
QUART_WORKERS=1

# Benchmarks
BENCHMARK_REQUESTS=100
BENCHMARK_TIMEOUT=30
```

### Modification des Workers

Éditez les `Dockerfile` respectifs:

```dockerfile
# Pour Flask
CMD ["gunicorn", "--workers", "4", "--threads", "4", ...]

# Pour Quart
CMD ["uvicorn", "--workers", "2", ...]
```

---

## 📈 Génération de Rapports

### Rapports Disponibles

Après `make report`:

1. **JSON:** `benchmarks/benchmark_results.json`
   - Données brutes pour analyse

2. **Markdown:** `benchmarks/BENCHMARK_RESULTS.md`
   - Tableaux de résultats

3. **Graphiques:** `benchmarks/benchmark_graphs/`
   - `concurrent_comparison.png` - Comparaison charge
   - `latency_percentiles.png` - Percentiles
   - `quart_speedup.png` - Speedup de Quart
   - `endpoint_comparison.png` - Par endpoint
   - `scalability.png` - Scalabilité
   - `summary.png` - Résumé visuel

---

## 🐛 Troubleshooting

### Les services ne démarrent pas

```bash
# Vérifier les logs
make logs

# Vérifier le status
make status

# Rebuild depuis zéro
make rebuild
```

### Erreur "port already in use"

```bash
# Trouver le processus
lsof -i :5001

# Tuer le processus ou changer le port dans docker-compose
```

### Benchmarks échouent

```bash
# Vérifier que les services sont up
make health

# Attendre que les services soient prêts
make check-services

# Relancer les tests
make test
```

---

## 📝 Licence

MIT License - Libre d'utilisation pour l'apprentissage et la démonstration.

---

## 🙏 Ressources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Quart Documentation](https://quart.palletsprojects.com/)
- [ASGI Specification](https://asgi.readthedocs.io/)
- [Python asyncio](https://docs.python.org/3/library/asyncio.html)

---

## ✨ Conclusion

**Le message clé:**

1. ✅ **Flask + WSGI:** Excellent pour CPU-bound et apps classiques
2. 🚫 **Flask + async sur WSGI:** NE PAS FAIRE - aucun bénéfice
3. 🚫 **Flask + ASGI wrapper:** NE PAS FAIRE - overhead sans bénéfice
4. ✅ **Quart:** Solution moderne pour I/O-bound avec async natif

**Règle simple:**
- Si vous avez besoin d'async → Utilisez Quart (ou FastAPI)
- Sinon → Flask WSGI fonctionne parfaitement

**N'utilisez PAS async avec Flask sur WSGI!** C'est un piège qui n'apporte rien.

---

Made with ❤️ for learning async/await in Python
