# 🚀 Démarrage Rapide

Guide ultra-rapide pour lancer la démo en 5 minutes!

## Option 1: Démarrage automatique

```bash
# Installation et démarrage automatique
./setup.sh
```

Le script va:
1. Vérifier les dépendances (Docker, Docker Compose)
2. Créer le fichier .env
3. Build les containers
4. Démarrer les services
5. Vérifier la santé des services

## Option 2: Démarrage manuel avec Make

```bash
# 1. Build les containers
make build

# 2. Démarrer tous les services
make up

# 3. Vérifier la santé
make health

# 4. Lancer une démo interactive
make demo
```

## Option 3: Docker Compose direct

```bash
# Note: Utilisez 'docker compose' (plugin moderne) ou 'docker-compose' (standalone)
# selon votre installation

# 1. Build
docker compose -f docker-compose.global.yml build
# ou: docker-compose -f docker-compose.global.yml build

# 2. Démarrer
docker compose -f docker-compose.global.yml up -d
# ou: docker-compose -f docker-compose.global.yml up -d

# 3. Vérifier
docker compose -f docker-compose.global.yml ps
# ou: docker-compose -f docker-compose.global.yml ps
```

## Test rapide

Une fois les services démarrés:

```bash
# Test simple
curl http://localhost:5001/health  # Flask WSGI
curl http://localhost:5004/health  # Quart

# Test de performance (requête lente de 1s)
time curl http://localhost:5001/slow
time curl http://localhost:5004/slow
```

## Benchmarks complets

```bash
# Lance tous les benchmarks et génère les graphiques
make report

# Résultats dans:
# - benchmarks/benchmark_results.json
# - benchmarks/BENCHMARK_RESULTS.md
# - benchmarks/benchmark_graphs/
```

## Présentation interactive

```bash
# Présentation dans le terminal
./presentation.py
```

## Commandes utiles

```bash
make help          # Voir toutes les commandes
make logs          # Voir les logs
make status        # Status des containers
make down          # Arrêter les services
make clean         # Nettoyer tout
```

## Accès aux services

Une fois lancés:

- **Flask WSGI:** http://localhost:5001
- **Flask Async:** http://localhost:5002
- **Flask+ASGI:** http://localhost:5003
- **Quart:** http://localhost:5004

## Endpoints disponibles

Sur chaque service:

- `/health` - Health check
- `/slow` - 1s sleep (I/O)
- `/multi-io` - 3×0.5s séquentiel
- `/cpu-intensive` - Calcul CPU
- `/db-simulation` - Simule DB query
- `/metrics` - Métriques du service

**Quart uniquement:**
- `/parallel` - Exécution parallèle
- `/sse` - Server-Sent Events
- `/ws` - WebSocket

## Résultats attendus

Avec 100 requêtes concurrentes sur `/slow`:

| Solution | Temps | RPS | Verdict |
|----------|-------|-----|---------|
| Flask WSGI | ~25s | 4.0 | ⚠️ Baseline |
| Flask Async | ~26s | 3.8 | 🚫 Pire! |
| Flask+ASGI | ~29s | 3.4 | 🚫 Le pire |
| **Quart** | **~1.2s** | **83.3** | ✅ **21x plus rapide!** |

## Troubleshooting

### Services ne démarrent pas

```bash
# Voir les logs
make logs

# Rebuild depuis zéro
make rebuild
```

### Port déjà utilisé

Modifiez les ports dans `docker-compose.global.yml`

### Tests échouent

```bash
# Attendre que les services soient prêts
make check-services

# Relancer
make test
```

## Prochaines étapes

1. 📖 Lisez le [README.md](README.md) complet
2. 🔍 Explorez le code des 4 implémentations
3. 📊 Analysez les résultats de benchmarks
4. 🚀 Testez avec vos propres endpoints

## Questions fréquentes

**Q: Puis-je utiliser Flask avec async?**
A: Non! Flask + async sur WSGI ne fonctionne pas. Utilisez Quart.

**Q: Quand utiliser Quart vs Flask?**
A: Quart pour I/O-bound (API calls, DB), Flask pour CPU-bound.

**Q: Comment migrer de Flask à Quart?**
A: L'API est quasi-identique! Voir la section migration dans le README.

---

**Besoin d'aide?** Consultez le [README.md](README.md) complet!
