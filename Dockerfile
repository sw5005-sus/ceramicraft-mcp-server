FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

# Update system packages to fix security vulnerabilities
RUN apt-get update && apt-get upgrade -y && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install dependencies first (cached layer)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy source code
COPY src/ src/
COPY README.md ./
RUN uv sync --frozen --no-dev

EXPOSE 8080

CMD ["uv", "run", "--no-dev", "python", "-m", "ceramicraft_mcp_server.serve"]
