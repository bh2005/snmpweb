FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends nmap ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# requests/urllib3 (genutzt fuer MIB-Downloads von mibs.pysnmp.com) bringen
# ihr eigenes certifi-Zertifikatsbuendel mit und ignorieren sonst zusaetzliche
# CAs, die per update-ca-certificates ins System eingebracht werden (z.B.
# bei TLS-Inspection durch einen Firmen-Proxy).
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend ./backend
COPY frontend ./frontend

WORKDIR /app/backend

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
