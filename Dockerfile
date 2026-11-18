FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Set working directory
WORKDIR /app

# Copy dependency files first to leverage cache
COPY pyproject.toml uv.lock ./

# Install dependencies into a virtualenv
RUN uv sync --frozen

COPY main.py ./

# Install dependencies using uv
RUN uv sync --frozen

# Expose port 8001
EXPOSE 8001

# Run the server
CMD ["uv", "run", "python", "main.py", "--host", "0.0.0.0", "--port", "8001"]
