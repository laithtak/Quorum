FROM python:3.12-slim

WORKDIR /app
COPY council-ai/ ./council-ai/
RUN pip install --no-cache-dir -e ./council-ai

ENTRYPOINT ["council"]
