FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Install gosu for safe root-to-user switching
RUN apt-get update && apt-get install -y gosu && rm -rf /var/lib/apt/lists/*

# Create a dedicated non-root user
RUN useradd -m -u 1000 mcpuser

# Create data directory and set ownership
RUN mkdir -p /data/pdfs && chown mcpuser:mcpuser /data/pdfs && chmod 775 /data/pdfs

# Set working directory
WORKDIR /app

# Copy dependency files first to leverage cache
COPY pyproject.toml uv.lock ./

# Install dependencies into a virtualenv as root (needed for system-level setup)
RUN uv sync --frozen

# Copy application code
COPY . .

# Ensure mcpuser owns the app directory
RUN chown -R mcpuser:mcpuser /app

# Switch to non-root user for runtime
USER mcpuser

# Expose port 8001
EXPOSE 8001

# Entrypoint script to handle bind mount permission issues
COPY --chown=mcpuser:mcpuser entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["uv", "run", "python", "main.py", "--host", "0.0.0.0", "--port", "8001"]
