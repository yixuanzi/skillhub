# SkillHub All-in-One Dockerfile
# Runs both backend (FastAPI) and frontend (React static) in a single container

# Stage 1: Build Frontend
# ...
# Stage 2: Backend with Frontend Static Files
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    nginx \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Create appuser
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy Python requirements first for better caching
COPY backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ /app/

# Create necessary directories and set permissions
RUN mkdir -p /app/data /var/log/supervisor \
    && chown -R appuser:appuser /app /var/log/supervisor

# Copy frontend build artifacts from frontend-builder
COPY frontend/dist /usr/share/nginx/html
RUN chown -R appuser:appuser /usr/share/nginx/html

# Copy supervisor configuration
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Copy nginx configuration
#COPY docker/nginx.conf /etc/nginx/sites-available/default
COPY docker/nginx.conf /etc/nginx/nginx.conf

# Expose ports (80 for frontend, 8000 for backend direct access)
EXPOSE 80 8000

# Health check - checks both nginx and backend
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/script/health && \
        curl -f http://localhost:80/ || exit 1

# Start supervisord to run both services
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
