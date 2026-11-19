FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY api/ ./api/
COPY model_registry.py .
COPY prediction.py .
COPY evaluation.py .

COPY artifacts/ ./artifacts/

RUN mkdir -p /app/reports
COPY reports/evaluation_report.json ./reports/evaluation_report.json

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
