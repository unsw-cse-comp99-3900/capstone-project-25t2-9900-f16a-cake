#!/usr/bin/env python3

"""
Clean Stress Test - Backend API Stress Testing Tool

This module provides a comprehensive stress testing framework for testing backend API performance and stability.
Key features include:

1. Concurrent User Simulation: Support for multiple users simultaneously accessing API endpoints
2. Endpoint Testing: Support for GET and POST requests with configurable test data and headers
3. Performance Monitoring: Records response time, success rate, error rate and other key metrics
4. System Resource Monitoring: Real-time monitoring of CPU and memory usage
5. Result Analysis: Generates detailed test reports including endpoint statistics and system metrics
6. Configuration Driven: Define test endpoints and parameters through JSON configuration files

Usage:
- Configure test_config_clean.json file to define test endpoints
- Run main() function to start stress testing
- Default test parameters: 300 seconds duration, 50 concurrent users
- Test results are automatically saved as JSON files

Version: 1.0
"""

import json
import time
import asyncio
import aiohttp
import psutil
from datetime import datetime
from typing import Dict, List

class CleanStressTest:
    def __init__(self, base_url: str = "http://localhost:8000", config_file: str = "test_config_clean.json"):
        self.base_url = base_url
        self.config_file = config_file
        self.endpoints = []
        self.results = {
            'test_info': {},
            'load_test': {},
            'system_metrics': [],
            'endpoint_stats': {}
        }
        
    def load_config(self):
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.endpoints = config.get('endpoints', [])
                print(f"Loaded {len(self.endpoints)} endpoints from {self.config_file}")
        except Exception as e:
            print(f"Failed to load config: {e}")
            return False
        return True
    
    async def test_endpoint(self, session: aiohttp.ClientSession, endpoint: Dict, user_id: int) -> Dict:
        path = endpoint['path']
        method = endpoint['method']
        test_data = endpoint.get('test_data', {})
        headers = endpoint.get('headers', {})
        
        start_time = time.time()
        
        try:
            if method == 'GET':
                async with session.get(f"{self.base_url}{path}", headers=headers, timeout=30) as response:
                    response_time = time.time() - start_time
                    return {
                        'endpoint': path,
                        'method': method,
                        'status_code': response.status,
                        'response_time': response_time,
                        'success': 200 <= response.status < 400,
                        'user_id': user_id
                    }
            elif method == 'POST':
                async with session.post(f"{self.base_url}{path}", json=test_data, headers=headers, timeout=30) as response:
                    response_time = time.time() - start_time
                    return {
                        'endpoint': path,
                        'method': method,
                        'status_code': response.status,
                        'response_time': response_time,
                        'success': 200 <= response.status < 400,
                        'user_id': user_id
                    }
            else:
                return {
                    'endpoint': path,
                    'method': method,
                    'status_code': None,
                    'response_time': 0,
                    'success': False,
                    'user_id': user_id,
                    'error': f'Unsupported method: {method}'
                }
        except Exception as e:
            response_time = time.time() - start_time
            return {
                'endpoint': path,
                'method': method,
                'status_code': None,
                'response_time': response_time,
                'success': False,
                'user_id': user_id,
                'error': str(e)
            }
    
    async def simulate_user(self, session: aiohttp.ClientSession, user_id: int, duration: int) -> List[Dict]:
        user_results = []
        start_time = time.time()
        
        while time.time() - start_time < duration:
            total_weight = sum(ep.get('weight', 1) for ep in self.endpoints)
            rand_weight = total_weight * (time.time() - start_time) / duration
            
            current_weight = 0
            selected_endpoint = None
            
            for endpoint in self.endpoints:
                current_weight += endpoint.get('weight', 1)
                if current_weight >= rand_weight:
                    selected_endpoint = endpoint
                    break
            
            if selected_endpoint:
                result = await self.test_endpoint(session, selected_endpoint, user_id)
                user_results.append(result)
                
                await asyncio.sleep(0.1)
        
        return user_results
    
    def collect_system_metrics(self):
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            return {
                'timestamp': datetime.now().isoformat(),
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available_mb': memory.available / (1024 * 1024)
            }
        except Exception as e:
            return {
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
    
    async def run_stress_test(self, duration: int = 300, concurrent_users: int = 50):
        print("Starting stress test...")
        print(f"Duration: {duration} seconds")
        print(f"Concurrent users: {concurrent_users}")
        print(f"Endpoints: {len(self.endpoints)}")
        print("=" * 60)
        
        monitoring_task = asyncio.create_task(self.monitor_system(duration))
        
        user_tasks = []
        async with aiohttp.ClientSession() as session:
            for user_id in range(concurrent_users):
                task = asyncio.create_task(self.simulate_user(session, user_id, duration))
                user_tasks.append(task)
            
            all_results = await asyncio.gather(*user_tasks)
        
        monitoring_task.cancel()
        
        self.process_results(all_results, duration, concurrent_users)
        
        return self.results
    
    async def monitor_system(self, duration: int):
        start_time = time.time()
        while time.time() - start_time < duration:
            metrics = self.collect_system_metrics()
            self.results['system_metrics'].append(metrics)
            await asyncio.sleep(5)
    
    def process_results(self, all_results: List[List[Dict]], duration: int, concurrent_users: int):
        all_requests = []
        for user_results in all_results:
            all_requests.extend(user_results)
        
        if not all_requests:
            return
        
        total_requests = len(all_requests)
        successful_requests = len([r for r in all_requests if r.get('success', False)])
        failed_requests = total_requests - successful_requests
        
        response_times = [r.get('response_time', 0) for r in all_requests if r.get('success', False)]
        
        endpoint_stats = {}
        for request in all_requests:
            endpoint = request['endpoint']
            if endpoint not in endpoint_stats:
                endpoint_stats[endpoint] = {
                    'total': 0,
                    'successful': 0,
                    'failed': 0,
                    'response_times': []
                }
            
            endpoint_stats[endpoint]['total'] += 1
            if request.get('success', False):
                endpoint_stats[endpoint]['successful'] += 1
                endpoint_stats[endpoint]['response_times'].append(request.get('response_time', 0))
            else:
                endpoint_stats[endpoint]['failed'] += 1
        
        for endpoint, stats in endpoint_stats.items():
            if stats['response_times']:
                stats['avg_response_time'] = sum(stats['response_times']) / len(stats['response_times'])
                stats['min_response_time'] = min(stats['response_times'])
                stats['max_response_time'] = max(stats['response_times'])
            else:
                stats['avg_response_time'] = 0
                stats['min_response_time'] = 0
                stats['max_response_time'] = 0
        
        self.results['test_info'] = {
            'duration': duration,
            'concurrent_users': concurrent_users,
            'start_time': datetime.now().isoformat()
        }
        
        self.results['load_test'] = {
            'total_requests': total_requests,
            'successful_requests': successful_requests,
            'failed_requests': failed_requests,
            'success_rate': successful_requests / total_requests if total_requests > 0 else 0,
            'error_rate': failed_requests / total_requests if total_requests > 0 else 0,
            'requests_per_second': total_requests / duration if duration > 0 else 0,
            'avg_response_time': sum(response_times) / len(response_times) if response_times else 0,
            'min_response_time': min(response_times) if response_times else 0,
            'max_response_time': max(response_times) if response_times else 0
        }
        
        self.results['endpoint_stats'] = endpoint_stats
    
    def print_results(self):
        print("\n" + "=" * 80)
        print("STRESS TEST RESULTS SUMMARY")
        print("=" * 80)
        
        load_test = self.results['load_test']
        print(f"Total Requests: {load_test['total_requests']:,}")
        print(f"Successful Requests: {load_test['successful_requests']:,}")
        print(f"Failed Requests: {load_test['failed_requests']:,}")
        print(f"Success Rate: {load_test['success_rate']:.2%}")
        print(f"Error Rate: {load_test['error_rate']:.2%}")
        print(f"Requests/Second: {load_test['requests_per_second']:.2f}")
        print(f"Average Response Time: {load_test['avg_response_time']:.3f}s")
        print(f"Min Response Time: {load_test['min_response_time']:.3f}s")
        print(f"Max Response Time: {load_test['max_response_time']:.3f}s")
        
        print(f"\nEndpoint Statistics:")
        for endpoint, stats in self.results['endpoint_stats'].items():
            success_rate = stats['successful'] / stats['total'] if stats['total'] > 0 else 0
            print(f"  {endpoint}:")
            print(f"    Total: {stats['total']}, Success: {stats['successful']}, Rate: {success_rate:.1%}")
            if stats['avg_response_time'] > 0:
                print(f"    Avg Time: {stats['avg_response_time']:.3f}s")
        
        if self.results['system_metrics']:
            print(f"\nSystem Metrics:")
            cpu_values = [m.get('cpu_percent', 0) for m in self.results['system_metrics'] if 'cpu_percent' in m]
            memory_values = [m.get('memory_percent', 0) for m in self.results['system_metrics'] if 'memory_percent' in m]
            
            if cpu_values:
                print(f"  CPU: Avg {sum(cpu_values)/len(cpu_values):.1f}%, Max {max(cpu_values):.1f}%")
            if memory_values:
                print(f"  Memory: Avg {sum(memory_values)/len(memory_values):.1f}%, Max {max(memory_values):.1f}%")
        
        print("=" * 80)
    
    def save_results(self, filename: str = "clean_stress_test_results.json"):
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)
            print(f"Results saved to: {filename}")
        except Exception as e:
            print(f"Failed to save results: {e}")

async def main():
    print("Clean Stress Test - Using test_config_clean.json")
    print("=" * 60)
    
    stress_tester = CleanStressTest()
    
    if not stress_tester.load_config():
        print("Failed to load configuration")
        return
    
    try:
        results = await stress_tester.run_stress_test(
            duration=300,
            concurrent_users=50
        )
        
        stress_tester.print_results()
        
        stress_tester.save_results()
        
        print("\nStress test completed successfully!")
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Error during stress test: {e}")

if __name__ == "__main__":
    asyncio.run(main())
