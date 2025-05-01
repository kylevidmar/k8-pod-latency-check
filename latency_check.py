#!/usr/bin/env python3
import subprocess
import json
import pandas as pd
import concurrent.futures
import time
import argparse
from kubernetes import client, config

def get_all_pods():
    """Get all pods in the Kubernetes cluster with their IPs."""
    config.load_incluster_config() 
    v1 = client.CoreV1Api()
    
    pods = v1.list_pod_for_all_namespaces(watch=False)
    pod_info = []
    
    for pod in pods.items:
        if pod.status.phase == "Running" and pod.status.pod_ip:
            pod_info.append({
                "namespace": pod.metadata.namespace,
                "name": pod.metadata.name,
                "ip": pod.status.pod_ip
            })
    
    return pod_info

def ping_pod(source_pod, target_pod, count=10):
    """Measure latency from source pod to target pod using ping."""
    cmd = [
        "kubectl", "exec", "-n", source_pod["namespace"], source_pod["name"], "--",
        "ping", "-c", str(count), "-q", target_pod["ip"]
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            # Extract average latency from ping output
            output = result.stdout
            if "avg" in output:
                # Parse the rtt min/avg/max/mdev line
                rtt_line = [line for line in output.split('\n') if "avg" in line][0]
                avg_latency = float(rtt_line.split('/')[4])
                return avg_latency
        
        return None
    except Exception as e:
        print(f"Error pinging from {source_pod['name']} to {target_pod['name']}: {str(e)}")
        return None

def tcping_pod(source_pod, target_pod, port=80, count=10):
    """Measure TCP connection latency to a specific port."""
    cmd = [
        "kubectl", "exec", "-n", source_pod["namespace"], source_pod["name"], "--",
        "tcping", "-c", str(count), "-p", str(port), target_pod["ip"]
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            # Extract average latency
            output = result.stdout
            if "avg" in output:
                avg_line = [line for line in output.split('\n') if "avg" in line][0]
                avg_latency = float(avg_line.split(':')[1].strip().split(' ')[0])
                return avg_latency
        
        return None
    except Exception as e:
        print(f"Error TCP pinging from {source_pod['name']} to {target_pod['name']}:{port}: {str(e)}")
        return None

def measure_http_latency(source_pod, target_pod, port=80, path="/", count=10):
    """Measure HTTP request latency between pods."""
    cmd = [
        "kubectl", "exec", "-n", source_pod["namespace"], source_pod["name"], "--",
        "curl", "-o", "/dev/null", "-s", "-w", "%{time_total}", 
        f"http://{target_pod['ip']}:{port}{path}"
    ]
    
    total_time = 0
    success_count = 0
    
    for _ in range(count):
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                time_taken = float(result.stdout.strip())
                total_time += time_taken
                success_count += 1
            
            time.sleep(0.1)  # Small delay between requests
            
        except Exception as e:
            print(f"Error HTTP request from {source_pod['name']} to {target_pod['name']}:{port}: {str(e)}")
    
    if success_count > 0:
        return (total_time * 1000) / success_count  # Convert to ms
    return None

def run_latency_tests(test_type="ping", port=80, path="/", count=5, output_format="table"):
    """Run latency tests between all pods using specified method."""
    pods = get_all_pods()
    results = []
    
    print(f"Found {len(pods)} pods in the cluster")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_pods = {}
        
        for source_pod in pods:
            for target_pod in pods:
                if source_pod["ip"] != target_pod["ip"]:
                    if test_type == "ping":
                        future = executor.submit(ping_pod, source_pod, target_pod, count)
                    elif test_type == "tcp":
                        future = executor.submit(tcping_pod, source_pod, target_pod, port, count)
                    elif test_type == "http":
                        future = executor.submit(measure_http_latency, source_pod, target_pod, port, path, count)
                    
                    future_to_pods[future] = (source_pod, target_pod)
        
        for future in concurrent.futures.as_completed(future_to_pods):
            source_pod, target_pod = future_to_pods[future]
            try:
                latency = future.result()
                if latency is not None:
                    results.append({
                        "source_namespace": source_pod["namespace"],
                        "source_pod": source_pod["name"],
                        "target_namespace": target_pod["namespace"],
                        "target_pod": target_pod["name"],
                        "latency_ms": latency
                    })
            except Exception as e:
                print(f"Error processing result: {str(e)}")
    
    # Sort results by latency (highest first)
    results.sort(key=lambda x: x["latency_ms"], reverse=True)
    
    # Output results in the requested format
    if output_format == "json":
        print(json.dumps(results, indent=2))
    elif output_format == "csv":
        df = pd.DataFrame(results)
        print(df.to_csv(index=False))
    else:  # table format
        df = pd.DataFrame(results)
        print(df.to_string(index=False))
    
    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Measure network latency between Kubernetes pods')
    parser.add_argument('--test-type', choices=['ping', 'tcp', 'http'], default='ping',
                        help='Type of latency test to perform (default: ping)')
    parser.add_argument('--port', type=int, default=80,
                        help='Port to use for TCP and HTTP tests (default: 80)')
    parser.add_argument('--path', default='/',
                        help='Path to use for HTTP tests (default: /)')
    parser.add_argument('--count', type=int, default=5,
                        help='Number of tests to run for each pod pair (default: 5)')
    parser.add_argument('--format', choices=['table', 'json', 'csv'], default='table',
                        help='Output format (default: table)')
    
    args = parser.parse_args()
    
    print(f"Starting {args.test_type} latency tests between all pods...")
    run_latency_tests(
        test_type=args.test_type,
        port=args.port,
        path=args.path,
        count=args.count,
        output_format=args.format
    )
