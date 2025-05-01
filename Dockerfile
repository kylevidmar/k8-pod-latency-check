FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    iputils-ping \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Install tcping for TCP connectivity testing
RUN curl -L https://github.com/mkirchner/tcping/archive/refs/tags/v1.3.6.tar.gz -o tcping.tar.gz && \
    tar -xzf tcping.tar.gz && \
    cd tcping-1.3.6 && \
    gcc -o /usr/local/bin/tcping tcping.c && \
    cd .. && \
    rm -rf tcping-1.3.6 tcping.tar.gz

# Copy the script
COPY latency_test.py .

# Copy RBAC configuration files
COPY rbac.yaml .
COPY latency-tester-pod.yaml .

# Make the script executable
RUN chmod +x latency_test.py

# Set environment variable for in-cluster config
ENV PYTHONUNBUFFERED=1

# Entrypoint script
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["--test-type", "ping", "--format", "table"]
