FROM python:3.11-slim
WORKDIR /app
# Assume repo mounted at /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONUTF8=1

# Install runtime deps if needed
RUN pip install --no-cache-dir pip

COPY . /app
RUN python -m pip install --no-cache-dir -r requirements.txt || true

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
