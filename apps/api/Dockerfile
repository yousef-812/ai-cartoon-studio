FROM python:3.11-slim
WORKDIR /workspace
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/workspace
COPY apps/api/pyproject.toml /workspace/apps/api/pyproject.toml
RUN pip install --no-cache-dir -e "/workspace/apps/api"
COPY apps/api /workspace/apps/api
COPY packages /workspace/packages
COPY workflows /workspace/workflows
WORKDIR /workspace/apps/api
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
