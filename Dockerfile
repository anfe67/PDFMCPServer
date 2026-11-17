FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy project files
COPY pyproject.toml ./
COPY main.py ./

# Install dependencies using uv
RUN uv sync --frozen

# Expose port 8001
EXPOSE 8001

# Run the server
CMD ["uv", "run", "python", "main.py"]
