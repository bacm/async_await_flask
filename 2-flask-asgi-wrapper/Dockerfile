FROM python:3.11-slim

WORKDIR /app

# Installation des dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie de l'application
COPY app.py .

# Exposition du port
EXPOSE 5000

# Hypercorn (recommandé par Flask pour ASGI wrapper)
# Meilleure gestion du WsgiToAsgi que Uvicorn
# Mais Flask en dessous reste synchrone!
CMD ["hypercorn", \
     "app:asgi_app", \
     "--bind", "0.0.0.0:5000", \
     "--workers", "4", \
     "--worker-class", "asyncio", \
     "--access-log", "-", \
     "--error-log", "-"]
