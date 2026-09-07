FROM node:20-alpine AS frontend

# K+S-Root/Zwischen-CA, damit npm hinter der TLS-Inspection des Firmenproxies
# funktioniert (der Proxy signiert ausgehende HTTPS-Verbindungen mit dieser CA).
COPY backend/certs/*.crt /usr/local/share/ca-certificates/
# apk selbst braucht ca-certificates fuer HTTPS, das ist hier noch nicht
# vorhanden (Henne-Ei) -> Alpine-Mirror kurz per HTTP statt HTTPS ansprechen,
# davon ist der Firmenproxy (TLS-Inspection nur bei HTTPS) nicht betroffen.
RUN sed -i 's/https:/http:/' /etc/apk/repositories \
    && apk add --no-cache ca-certificates \
    && update-ca-certificates
ENV NODE_EXTRA_CA_CERTS=/etc/ssl/certs/ca-certificates.crt

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends nmap ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# K+S-Root/Zwischen-CA (siehe frontend-Stage) fuer pip sowie fuer
# requests/urllib3 (genutzt fuer MIB-Downloads von mibs.pysnmp.com), die
# sonst ihr eigenes certifi-Zertifikatsbuendel nutzen und zusaetzliche CAs
# aus update-ca-certificates ignorieren wuerden.
COPY backend/certs/*.crt /usr/local/share/ca-certificates/
RUN update-ca-certificates
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt
ENV PIP_CERT=/etc/ssl/certs/ca-certificates.crt

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend ./backend
COPY --from=frontend /app/frontend/dist ./frontend/dist

WORKDIR /app/backend

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
