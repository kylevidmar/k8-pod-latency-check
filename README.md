# Kubernetes Pod Latency Tester

A Python utility for measuring network latency between pods in a Kubernetes cluster with a focus on identifying performance bottlenecks.

## Features

- Measures latency between all pods in a Kubernetes cluster
- Supports multiple testing methods:
  - ICMP ping (basic network connectivity)
  - TCP connection time (application connectivity)
  - HTTP request latency (full application request)
- Concurrent testing for faster results
- Multiple output formats (table, JSON, CSV)
- Sorted results to quickly identify highest latency connections

## Prerequisites

- Access to a Kubernetes cluster
- `kubectl` installed and configured
- Python 3.6+
- Appropriate RBAC permissions to list pods and execute commands in them

## Installation

1. Clone this repository:
```
git clone https://github.com/yourusername/k8s-latency-tester.git
cd k8s-latency-tester
```

2. Install required dependencies:
```
pip install -r requirements.txt
```

3. Create necessary RBAC permissions in your cluster:
```
kubectl apply -f rbac.yaml
```

## Usage

### Running as a standalone script

```bash
python latency_test.py --test-type ping --format table
```

### Running in a Kubernetes pod

1. Create a ConfigMap with the script:
```
kubectl create configmap latency-test-script --from-file=latency_test.py
```

2. Deploy the tester pod:
```
kubectl apply -f latency-tester-pod.yaml
```

3. Execute the script in the pod:
```
kubectl exec -it network-latency-tester -- python /app/latency_test.py --test-type http --format json
```

## Command Line Options

- `--test-type`: Type of latency test to perform (choices: ping, tcp, http; default: ping)
- `--port`: Port to use for TCP and HTTP tests (default: 80)
- `--path`: Path to use for HTTP tests (default: /)
- `--count`: Number of tests to run for each pod pair (default: 5)
- `--format`: Output format (choices: table, json, csv; default: table)

## Example Output

```
                              source_namespace source_pod       target_namespace   target_pod     latency_ms
                                    default     app-pod-1            monitoring  metrics-pod        12.458
                                    default     app-pod-2               logging     log-pod         8.237
                                 monitoring  metrics-pod               default     app-pod-1        7.891
                                    logging     log-pod                default     app-pod-2        6.543
...
```

## Troubleshooting

- Ensure your service account has appropriate permissions to list pods and execute commands
- For TCP/HTTP tests, verify the target pods are listening on the specified ports
- If using `tcping` for TCP tests, make sure it's installed in your pods

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
