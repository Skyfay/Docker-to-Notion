# Verwende ein offizielles Python-Image als Basis
FROM python:3.10-slim

# Setze das Arbeitsverzeichnis im Container
WORKDIR /app

# Installiere grundlegende Pakete
RUN apt-get update && apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    bash \
    build-essential

# Installiere Docker CLI und Docker Compose
RUN apt-get install -y \
    sudo && \
    # Erstelle das Verzeichnis für die GPG-Schlüssel
    install -m 0755 -d /etc/apt/keyrings && \
    # Docker GPG-Schlüssel hinzufügen
    curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc && \
    chmod a+r /etc/apt/keyrings/docker.asc && \
    # Docker-Repository hinzufügen
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian \
    $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null && \
    apt-get update && \
    # Docker und Docker Compose installieren
    apt-get install -y \
    docker-ce \
    docker-ce-cli \
    containerd.io \
    docker-buildx-plugin \
    docker-compose-plugin

# Installiere crane
RUN curl -LO "https://github.com/google/go-containerregistry/releases/download/v0.20.2/go-containerregistry_Linux_x86_64.tar.gz" && \
    tar -xzf go-containerregistry_Linux_x86_64.tar.gz crane && \
    mv crane /usr/local/bin/ && \
    rm go-containerregistry_Linux_x86_64.tar.gz

# Bereinige APT-Daten
RUN apt-get clean && rm -rf /var/lib/apt/lists/*

# Kopiere die requirements.txt in das Arbeitsverzeichnis
COPY requirements.txt /app/

# Installiere die Python-Abhängigkeiten
RUN pip install --no-cache-dir -r requirements.txt

# Kopiere den gesamten Anwendungscode aus dem src-Verzeichnis in das Arbeitsverzeichnis
COPY src/ /app/

# Umgebungsvariable setzen (falls erforderlich)
ENV PYTHONUNBUFFERED=1

# Starte das Hauptskript
CMD ["python", "main.py"]
