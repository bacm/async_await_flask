FROM python:3.11-slim

WORKDIR /app

# Installation des dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie de l'application
COPY app.py .

# Exposition du port
EXPOSE 5000

# Uvicorn avec Quart - véritable async ASGI natif!
# Un seul worker peut gérer des centaines de requêtes concurrentes
CMD ["uvicorn", \
     "app:app", \
     "--host", "0.0.0.0", \
     "--port", "5000", \
     "--workers", "1", \
     "--log-level", "info"]
