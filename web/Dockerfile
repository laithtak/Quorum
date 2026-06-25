FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY web/frontend/package.json ./
RUN npm install
COPY web/frontend/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
COPY council-ai/ ./council-ai/
RUN pip install --no-cache-dir -e "./council-ai[web]"
COPY web/api/ ./web/api/
COPY --from=frontend-build /app/frontend/dist ./web/frontend/dist
ENV PYTHONPATH=/app
EXPOSE 8000
CMD ["uvicorn", "web.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
