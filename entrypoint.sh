#!/bin/bash
set -e

# Check if we're running in debug mode
if [ "$1" = "debug" ]; then
    echo "Starting in debug mode..."
    exec /bin/bash
fi

# Check if we're asked to apply RBAC
if [ "$1" = "apply-rbac" ]; then
    echo "Applying RBAC configuration..."
    kubectl apply -f rbac.yaml
    exit 0
fi

# Check if we're asked to deploy the tester pod
if [ "$1" = "deploy" ]; then
    echo "Deploying latency tester pod..."
    kubectl apply -f latency-tester-pod.yaml
    exit 0
fi

# Otherwise, run the latency test script with all arguments passed to the container
echo "Running latency test with arguments: $@"
exec python /app/latency_test.py "$@"
