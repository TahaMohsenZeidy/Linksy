FROM python:3.13-slim
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

# Copy application code
COPY ./src /app/src
COPY ./alembic.ini /app/alembic.ini
COPY ./alembic/ /app/alembic/

# Use entrypoint script (runs migrations and starts app)
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]