FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.lock ./
RUN python -m pip install --no-cache-dir -r requirements.lock
COPY pyproject.toml alembic.ini ./
COPY src ./src
COPY migrations ./migrations
COPY configs ./configs
COPY ui ./ui
RUN python -m pip install --no-cache-dir --no-deps .
RUN useradd --create-home --uid 10001 compliance
USER compliance
