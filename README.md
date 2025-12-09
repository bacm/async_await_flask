# Flask vs Quart: Async/Await Démonstration

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-3.0.0-green.svg)](https://flask.palletsprojects.com/)
[![Quart](https://img.shields.io/badge/Quart-0.19.4-blue.svg)](https://quart.palletsprojects.com/)
[![Docker](https://img.shields.io/badge/Docker-ready-blue.svg)](https://www.docker.com/)

**Projet de démonstration complet** pour comprendre les différences entre Flask (WSGI), Flask+ASGI wrapper, et Quart (ASGI natif).

## 📋 Table des matières

- [Le Problème](#-le-problème)
- [Les Solutions Comparées](#-les-solutions-comparées)
- [Structure du Projet](#-structure-du-projet)
- [Installation et Utilisation](#-installation-et-utilisation)
- [Résultats Attendus](#-résultats-attendus)
- [Explications Détaillées](#-explications-détaillées)

---

## 🎯 Le Problème

### Définition
`async/await` permet de mettre une fonction en pause en attendant une opération non bloquante, sans arrêter le thread.
Pendant cette pause, l’event loop — une boucle centrale qui orchestre toutes les tâches asynchrones — continue d’exécuter d’autres tâches et reprend la fonction dès que le résultat est prêt.

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

### 2️⃣ Flask + ASGI Wrapper (SOLUTION INTERMÉDIAIRE)

**Utiliser `asgiref` pour wrapper Flask:**

```python
from flask import Flask
from asgiref.wsgi import WsgiToAsgi

app = Flask(__name__)
asgi_app = WsgiToAsgi(app)  # Wrapper WSGI → ASGI
```

**Les avantages:**
- ✅ Permet d'utiliser async/await dans Flask
- ✅ **30-40% plus rapide** que WSGI pur pour les workloads I/O-bound
- ✅ Migration progressive possible
- ✅ Garde la compatibilité avec l'écosystème Flask

**Les limites:**
- ⚠️ Léger overhead de conversion (mais compensé par les gains async)
- ⚠️ Pas aussi performant que Quart natif (3-4x plus lent que Quart)

**Verdict:** ✅ **Bonne solution intermédiaire** pour migrer progressivement vers async

---

### 3️⃣ Quart (LA BONNE SOLUTION! ✨)

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
├── 2-flask-asgi-wrapper/      # Flask + wrapper ASGI (mauvais)
│   ├── app.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── 3-quart-native/            # Quart natif (solution!)
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
- **Flask ASGI Wrapper:** http://localhost:5002
- **Quart Native:** http://localhost:5003

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
| **Flask WSGI** | 16.2s | 6.2 | 14.9s | ⚠️ Baseline synchrone |
| **Flask + ASGI** | 9.8s | 10.2 | 8.5s | ✅ **40% plus rapide que WSGI!** |
| **Quart Native** | 1.3s | 76.3 | 1.1s | ✅ **12x plus rapide que WSGI!** |

### ⚠️ Découverte Critique: `/slow` vs `/parallel`

**Test: 10 Requêtes Concurrentes sur `/slow` (I/O séquentiel simple)**

Le endpoint `/slow` fait un seul `await asyncio.sleep(0.25)` sans parallélisation.

| Solution | Temps Total | RPS | Verdict |
|----------|-------------|-----|---------|
| **Flask WSGI** | 1.10s | 9.1 | ⚠️ Baseline |
| **Flask + ASGI** | 1.62s | 6.2 | 🚫 **47% PLUS LENT!** |
| **Quart Native** | 0.37s | 27.1 | ✅ **3x plus rapide** |

**Comparaison avec `/parallel` (10 requêtes concurrentes):**

Le endpoint `/parallel` utilise `asyncio.gather()` pour paralléliser deux opérations I/O.

| Solution | Temps Total | RPS | Verdict |
|----------|-------------|-----|---------|
| **Flask WSGI** | 2.10s | 4.8 | ⚠️ Baseline |
| **Flask + ASGI** | 1.12s | 8.9 | ✅ **47% plus rapide!** |
| **Quart Native** | 0.37s | 27.3 | ✅ **5.7x plus rapide** |

**🔑 Enseignement Clé:**

- **Flask + ASGI wrapper** est bénéfique UNIQUEMENT avec `asyncio.gather()` ou parallélisation interne
- Pour des opérations I/O séquentielles simples, l'overhead du wrapper **pénalise** les performances
- **Quart** reste optimal dans tous les cas grâce à son implémentation ASGI native

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

### Comment le Wrapper ASGI Fonctionne?

`WsgiToAsgi` convertit une app WSGI en ASGI et permet l'utilisation d'async/await:

1. **Conversion ASGI ↔ WSGI**
   - Conversion request ASGI → WSGI
   - Conversion response WSGI → ASGI
   - Léger overhead CPU (mais compensé par les gains async)

2. **Async/await fonctionne réellement!**
   - Les routes async avec `await` libèrent vraiment le worker
   - **30-40% d'amélioration** sur les workloads I/O-bound
   - Concurrence réelle grâce à l'event loop ASGI

3. **Un bon compromis**
   - Garde l'écosystème Flask
   - Bénéficie de async pour I/O
   - Migration progressive vers Quart possible

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

### Utilisez Flask + ASGI wrapper si:

- ✅ Migration progressive depuis Flask WSGI
- ✅ Besoin de garder l'écosystème Flask
- ✅ Opérations I/O-bound **avec parallélisation** (`asyncio.gather()`) - 30-40% d'amélioration
- ✅ Ne pouvez pas migrer vers Quart immédiatement
- ⚠️ **ATTENTION:** Pour I/O séquentiels simples, peut être plus lent que WSGI!

### Utilisez Quart (ASGI) si:

- ✅ Beaucoup d'appels API externes
- ✅ Requêtes base de données fréquentes
- ✅ Besoin de WebSocket ou SSE
- ✅ Charge haute avec peu de ressources
- ✅ Opérations I/O bound (performance maximale)

### N'utilisez JAMAIS:

- 🚫 async/await pour du code CPU-bound pur (sans asyncio.to_thread)

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
2. ⚠️ **Flask + ASGI wrapper:** Bonne solution **SI** vous utilisez `asyncio.gather()` pour paralléliser
   - ✅ Avec parallélisation: +40% performance
   - 🚫 Sans parallélisation: -47% performance (overhead)
3. ✅ **Quart:** Solution optimale pour I/O-bound avec async natif (+1200% performance)

**Règle simple:**
- **Nouveau projet I/O-bound** → Utilisez Quart (ou FastAPI)
- **Migration progressive AVEC parallélisation async** → Flask + ASGI wrapper peut aider
- **I/O séquentiels simples** → Restez sur Flask WSGI ou migrez vers Quart
- **App CPU-bound ou simple** → Flask WSGI fonctionne parfaitement

**Échelle de performance pour I/O-bound avec parallélisation (100 requêtes concurrentes):**
- Flask WSGI: 16.2s (baseline)
- Flask + ASGI: 9.8s (**1.7x plus rapide**)
- Quart: 1.3s (**12.4x plus rapide**)

---

Made with ❤️ for learning async/await in Python
