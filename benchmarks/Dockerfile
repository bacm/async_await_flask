FROM python:3.11-slim

WORKDIR /app

# Installation des dépendances système pour matplotlib
RUN apt-get update && apt-get install -y \
    libfreetype6-dev \
    libpng-dev \
    && rm -rf /var/lib/apt/lists/*

# Installation des dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie des scripts
COPY test_all.py .
COPY visual_benchmark.py .

# Scripts exécutables
RUN chmod +x test_all.py visual_benchmark.py

CMD ["python", "test_all.py"]
