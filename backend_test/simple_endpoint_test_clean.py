#!/usr/bin/env python3
"""
Simple Endpoint Availability Test (Clean Version)
Check if all working API endpoints are accessible and responding
"""

import json
import time
import requests
from typing import Dict, List

class SimpleEndpointTester:
    """Simple tester for checking endpoint availability"""
    
    def __init__(self, base_url: str = "http://localhost:8000", config_file: str = "test_config_clean.json"):
        self.base_url = base_url
        self.config_file = config_file
        self.results = []
        self.session = requests.Session()
        
        # Set default headers
        self.session.headers.update({
            'User-Agent': 'SimpleEndpointTester/1.0',
            'Accept': 'application/json, text/plain, */*'
        })
    
    def load_endpoints(self) -> List[Dict]:
        """Load endpoints from config file"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('endpoints', [])
        except FileNotFoundError:
            print(f"ERROR: {self.config_file} not found")
            return []
        except json.JSONDecodeError:
            print(f"ERROR: Invalid JSON in {self.config_file}")
            return []
    
    def test_single_endpoint(self, endpoint: Dict) -> Dict:
        """Test a single endpoint"""
        path = endpoint['path']
        method = endpoint['method']
        description = endpoint.get('description', 'No description')
        
        print(f"Testing: {method} {path}")
        print(f"   Description: {description}")
        
        start_time = time.time()
        
        try:
            # Prepare request data
            test_data = endpoint.get('test_data', {})
            headers = endpoint.get('headers', {})
            
            # Make request
            if method == 'GET':
                response = self.session.get(
                    f"{self.base_url}{path}",
                    headers=headers,
                    timeout=10
                )
            elif method == 'POST':
                response = self.session.post(
                    f"{self.base_url}{path}",
                    json=test_data,
                    headers=headers,
                    timeout=10
                )
            elif method == 'DELETE':
                response = self.session.delete(
                    f"{self.base_url}{path}",
                    headers=headers,
                    timeout=10
                )
            else:
                return {
                    'endpoint': path,
                    'method': method,
                    'status_code': None,
                    'response_time': 0,
                    'success': False,
                    'error': f'Unsupported method: {method}',
                    'description': description
                }
            
            response_time = time.time() - start_time
            
            # Determine success (2xx and 3xx are considered successful for availability test)
            success = 200 <= response.status_code < 400
            
            result = {
                'endpoint': path,
                'method': method,
                'status_code': response.status_code,
                'response_time': round(response_time, 3),
                'success': success,
                'description': description,
                'error': None if success else f'HTTP {response.status_code}'
            }
            
            if success:
                print(f"   SUCCESS: {response.status_code} ({response_time:.3f}s)")
            else:
                print(f"   FAILED: {response.status_code} ({response_time:.3f}s)")
            
            return result
            
        except requests.exceptions.ConnectionError:
            response_time = time.time() - start_time
            print(f"   ERROR: Connection Error: Cannot connect to {self.base_url}")
            return {
                'endpoint': path,
                'method': method,
                'status_code': None,
                'response_time': round(response_time, 3),
                'success': False,
                'description': description,
                'error': 'Connection Error - Server not reachable'
            }
        except requests.exceptions.Timeout:
            response_time = time.time() - start_time
            print(f"   TIMEOUT: Request took too long")
            return {
                'endpoint': path,
                'method': method,
                'status_code': None,
                'response_time': round(response_time, 3),
                'success': False,
                'description': description,
                'error': 'Timeout - Request took too long'
            }
        except Exception as e:
            response_time = time.time() - start_time
            print(f"   ERROR: {str(e)}")
            return {
                'endpoint': path,
                'method': method,
                'status_code': None,
                'response_time': round(response_time, 3),
                'success': False,
                'description': description,
                'error': str(e)
            }
    
    def test_all_endpoints(self) -> List[Dict]:
        """Test all endpoints"""
        print("=" * 80)
        print("SIMPLE ENDPOINT AVAILABILITY TEST (CLEAN VERSION)")
        print("=" * 80)
        print(f"Base URL: {self.base_url}")
        print(f"Config File: {self.config_file}")
        print("=" * 80)
        
        endpoints = self.load_endpoints()
        if not endpoints:
            print("ERROR: No endpoints found to test")
            return []
        
        print(f"Found {len(endpoints)} endpoints to test")
        print("=" * 80)
        
        results = []
        for i, endpoint in enumerate(endpoints, 1):
            print(f"\n[{i}/{len(endpoints)}] ", end="")
            result = self.test_single_endpoint(endpoint)
            results.append(result)
            
            # Small delay between requests
            time.sleep(0.1)
        
        self.results = results
        return results
    
    def generate_summary_report(self) -> str:
        """Generate a summary report"""
        if not self.results:
            return "No test results available"
        
        total_endpoints = len(self.results)
        successful_endpoints = len([r for r in self.results if r['success']])
        failed_endpoints = total_endpoints - successful_endpoints
        
        # Group by status
        status_groups = {}
        for result in self.results:
            status = result['status_code'] if result['status_code'] else 'Connection Error'
            if status not in status_groups:
                status_groups[status] = []
            status_groups[status].append(result)
        
        # Generate report
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("ENDPOINT AVAILABILITY TEST SUMMARY (CLEAN VERSION)")
        report_lines.append("=" * 80)
        report_lines.append(f"Test Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"Base URL: {self.base_url}")
        report_lines.append(f"Config File: {self.config_file}")
        report_lines.append("")
        report_lines.append("OVERALL RESULTS:")
        report_lines.append(f"  Total Endpoints: {total_endpoints}")
        report_lines.append(f"  SUCCESSFUL: {successful_endpoints}")
        report_lines.append(f"  FAILED: {failed_endpoints}")
        report_lines.append(f"  SUCCESS RATE: {successful_endpoints/total_endpoints:.1%}")
        report_lines.append("")
        
        # Status breakdown
        report_lines.append("STATUS CODE BREAKDOWN:")
        for status, endpoints in status_groups.items():
            count = len(endpoints)
            percentage = count / total_endpoints * 100
            report_lines.append(f"  {status}: {count} endpoints ({percentage:.1f}%)")
        report_lines.append("")
        
        # Failed endpoints details
        if failed_endpoints > 0:
            report_lines.append("FAILED ENDPOINTS:")
            for result in self.results:
                if not result['success']:
                    report_lines.append(f"  FAILED: {result['method']} {result['endpoint']}")
                    report_lines.append(f"      Error: {result['error']}")
                    report_lines.append(f"      Description: {result['description']}")
            report_lines.append("")
        
        # Successful endpoints
        if successful_endpoints > 0:
            report_lines.append("SUCCESSFUL ENDPOINTS:")
            for result in self.results:
                if result['success']:
                    report_lines.append(f"  SUCCESS: {result['method']} {result['endpoint']}")
                    report_lines.append(f"      Status: {result['status_code']}")
                    report_lines.append(f"      Response Time: {result['response_time']}s")
            report_lines.append("")
        
        # Response time statistics
        successful_times = [r['response_time'] for r in self.results if r['success']]
        if successful_times:
            avg_time = sum(successful_times) / len(successful_times)
            min_time = min(successful_times)
            max_time = max(successful_times)
            report_lines.append("RESPONSE TIME STATISTICS (Successful requests):")
            report_lines.append(f"  Average: {avg_time:.3f}s")
            report_lines.append(f"  Minimum: {min_time:.3f}s")
            report_lines.append(f"  Maximum: {max_time:.3f}s")
            report_lines.append("")
        
        report_lines.append("=" * 80)
        
        return "\n".join(report_lines)
    
    def save_results(self, filename: str = "endpoint_availability_results_clean.json"):
        """Save test results to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)
            print(f"Results saved to: {filename}")
        except Exception as e:
            print(f"ERROR: Failed to save results: {e}")

def main():
    """Main function"""
    print("Simple Endpoint Availability Tester (Clean Version)")
    print("=" * 60)
    
    # Use default base URL and clean config
    base_url = "http://localhost:8000"
    config_file = "test_config.json"
    print(f"Using base URL: {base_url}")
    print(f"Using config file: {config_file}")
    
    # Create tester and run tests
    tester = SimpleEndpointTester(base_url, config_file)
    
    try:
        # Test all endpoints
        results = tester.test_all_endpoints()
        
        if results:
            # Generate and display summary
            summary = tester.generate_summary_report()
            print("\n" + summary)
            
            # Save results
            tester.save_results()
            
            print("\nEndpoint availability test completed!")
            print("Check the summary above for results.")
            
        else:
            print("ERROR: No endpoints were tested")
            
    except KeyboardInterrupt:
        print("\nWARNING: Test interrupted by user")
    except Exception as e:
        print(f"ERROR: Error during testing: {e}")

if __name__ == "__main__":
    main()
