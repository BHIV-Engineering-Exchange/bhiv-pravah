#!/usr/bin/env python3
"""
BHIV HR Platform - Master Test Runner
Executes all comprehensive tests and generates unified report
"""

import json
import time
from datetime import datetime
from pathlib import Path
import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from comprehensive_system_test import ComprehensiveSystemTester
from integration_reliability_test import IntegrationReliabilityTester

class MasterTestRunner:
    def __init__(self):
        self.results = {
            'test_suite': 'BHIV HR Platform - Complete System Validation',
            'timestamp': datetime.now().isoformat(),
            'comprehensive_test': {},
            'integration_test': {},
            'unified_summary': {},
            'recommendations': []
        }

    def run_all_tests(self):
        """Execute all test suites"""
        print("BHIV HR Platform - Master Test Execution")
        print("=" * 80)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        # 1. Run Comprehensive System Test
        print("\nPHASE 1: Comprehensive System Test")
        print("-" * 50)
        
        try:
            comprehensive_tester = ComprehensiveSystemTester()
            self.results['comprehensive_test'] = comprehensive_tester.run_comprehensive_test()
            comprehensive_tester.print_results()
        except Exception as e:
            print(f"ERROR: Comprehensive test failed: {str(e)}")
            self.results['comprehensive_test'] = {'error': str(e)}
        
        print("\n" + "=" * 50)
        
        # 2. Run Integration & Reliability Test
        print("\nPHASE 2: Integration & Reliability Test")
        print("-" * 50)
        
        try:
            integration_tester = IntegrationReliabilityTester()
            self.results['integration_test'] = integration_tester.run_integration_reliability_test()
            integration_tester.print_results()
        except Exception as e:
            print(f"ERROR: Integration test failed: {str(e)}")
            self.results['integration_test'] = {'error': str(e)}
        
        # 3. Generate Unified Summary
        self.generate_unified_summary()
        
        # 4. Print Final Report
        self.print_final_report()
        
        # 5. Save Results
        self.save_results()

    def generate_unified_summary(self):
        """Generate unified summary from all test results"""
        summary = {
            'overall_health': 'Unknown',
            'critical_issues': [],
            'warnings': [],
            'performance_metrics': {},
            'service_status': {},
            'database_status': 'Unknown',
            'integration_status': 'Unknown',
            'recommendations': []
        }
        
        # Analyze comprehensive test results
        comp_test = self.results.get('comprehensive_test', {})
        if 'summary' in comp_test:
            comp_summary = comp_test['summary']
            
            # Database status
            summary['database_status'] = 'Healthy' if comp_summary.get('database_healthy') else 'Unhealthy'
            
            # Service status
            services_healthy = comp_summary.get('services_healthy', 0)
            total_services = comp_summary.get('total_services_tested', 0)
            
            if total_services > 0:
                health_percentage = (services_healthy / total_services) * 100
                if health_percentage >= 90:
                    summary['overall_health'] = 'Excellent'
                elif health_percentage >= 75:
                    summary['overall_health'] = 'Good'
                elif health_percentage >= 50:
                    summary['overall_health'] = 'Fair'
                else:
                    summary['overall_health'] = 'Poor'
            
            # Performance metrics
            summary['performance_metrics']['avg_response_time'] = comp_summary.get('avg_response_time', 0)
            summary['performance_metrics']['endpoints_success_rate'] = (
                comp_summary.get('total_endpoints_passed', 0) / 
                max(1, comp_summary.get('total_endpoints_tested', 1))
            ) * 100
        
        # Analyze integration test results
        int_test = self.results.get('integration_test', {})
        if 'integration' in int_test:
            data_flow = int_test['integration'].get('data_flow', {})
            interconnections = int_test['integration'].get('interconnections', {})
            
            # Integration status
            data_flow_success = data_flow.get('success', False)
            interconnection_success = sum(1 for v in interconnections.values() if isinstance(v, bool) and v)
            total_interconnections = sum(1 for v in interconnections.values() if isinstance(v, bool))
            
            if data_flow_success and interconnection_success >= total_interconnections * 0.8:
                summary['integration_status'] = 'Excellent'
            elif data_flow_success or interconnection_success >= total_interconnections * 0.6:
                summary['integration_status'] = 'Good'
            else:
                summary['integration_status'] = 'Poor'
        
        # Generate recommendations
        if summary['database_status'] == 'Unhealthy':
            summary['critical_issues'].append('Database connectivity issues detected')
            summary['recommendations'].append('Investigate database connection and credentials')
        
        if summary['overall_health'] in ['Poor', 'Fair']:
            summary['critical_issues'].append('Multiple service health issues')
            summary['recommendations'].append('Review service logs and deployment status')
        
        if summary['performance_metrics'].get('avg_response_time', 0) > 2.0:
            summary['warnings'].append('High average response times detected')
            summary['recommendations'].append('Optimize service performance and database queries')
        
        if summary['integration_status'] == 'Poor':
            summary['critical_issues'].append('Service integration failures')
            summary['recommendations'].append('Check service interconnections and API endpoints')
        
        # Performance-based recommendations
        if 'performance' in int_test:
            load_test = int_test['performance'].get('concurrent_load', {})
            success_rate = (load_test.get('successful_requests', 0) / max(1, load_test.get('total_requests', 1))) * 100
            
            if success_rate < 95:
                summary['warnings'].append(f'Concurrent load success rate: {success_rate:.1f}%')
                summary['recommendations'].append('Consider scaling resources for better load handling')
        
        self.results['unified_summary'] = summary

    def print_final_report(self):
        """Print comprehensive final report"""
        print("\n" + "=" * 80)
        print("FINAL COMPREHENSIVE REPORT")
        print("=" * 80)
        
        summary = self.results['unified_summary']
        
        # Overall Status
        health_status = {
            'Excellent': '[EXCELLENT]',
            'Good': '[GOOD]', 
            'Fair': '[FAIR]',
            'Poor': '[POOR]',
            'Unknown': '[UNKNOWN]'
        }
        
        print(f"\nOVERALL SYSTEM HEALTH: {health_status.get(summary['overall_health'], '[UNKNOWN]')} {summary['overall_health']}")
        
        # Key Metrics
        print(f"\nKEY METRICS:")
        perf = summary.get('performance_metrics', {})
        print(f"   Average Response Time: {perf.get('avg_response_time', 0):.3f}s")
        print(f"   Endpoint Success Rate: {perf.get('endpoints_success_rate', 0):.1f}%")
        print(f"   Database Status: {summary['database_status']}")
        print(f"   Integration Status: {summary['integration_status']}")
        
        # Service Details
        comp_test = self.results.get('comprehensive_test', {})
        if 'services' in comp_test:
            print(f"\nSERVICE STATUS:")
            for service, results in comp_test['services'].items():
                passed = results.get('endpoints_passed', 0)
                total = results.get('endpoints_tested', 0)
                status = "[OK]" if passed > total * 0.8 else "[WARN]" if passed > total * 0.5 else "[FAIL]"
                print(f"   {service}: {status} ({passed}/{total} endpoints)")
        
        # Database Details
        if 'database' in comp_test:
            db = comp_test['database']
            print(f"\nDATABASE STATUS:")
            print(f"   Connection: {'[OK]' if db.get('connection') else '[FAIL]'}")
            for table, count in db.get('data_counts', {}).items():
                print(f"   {table}: {count} records")
        
        # Integration Details
        int_test = self.results.get('integration_test', {})
        if 'integration' in int_test:
            print(f"\nINTEGRATION STATUS:")
            interconnections = int_test['integration'].get('interconnections', {})
            for connection, status in interconnections.items():
                if isinstance(status, bool):
                    emoji = "[OK]" if status else "[FAIL]"
                    print(f"   {connection.replace('_', ' ').title()}: {emoji}")
        
        # Performance Details
        if 'performance' in int_test:
            load_test = int_test['performance'].get('concurrent_load', {})
            print(f"\nPERFORMANCE STATUS:")
            print(f"   Concurrent Users Tested: {load_test.get('concurrent_users', 0)}")
            print(f"   Total Requests: {load_test.get('total_requests', 0)}")
            print(f"   Success Rate: {(load_test.get('successful_requests', 0) / max(1, load_test.get('total_requests', 1))) * 100:.1f}%")
            print(f"   Throughput: {load_test.get('throughput', 0):.2f} req/sec")
        
        # Critical Issues
        if summary['critical_issues']:
            print(f"\nCRITICAL ISSUES:")
            for issue in summary['critical_issues']:
                print(f"   • {issue}")
        
        # Warnings
        if summary['warnings']:
            print(f"\nWARNINGS:")
            for warning in summary['warnings']:
                print(f"   • {warning}")
        
        # Recommendations
        if summary['recommendations']:
            print(f"\nRECOMMENDATIONS:")
            for rec in summary['recommendations']:
                print(f"   • {rec}")
        
        print("\n" + "=" * 80)
        print(f"Test Suite Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

    def save_results(self):
        """Save all test results to files"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save unified results
        unified_file = f'unified_test_results_{timestamp}.json'
        with open(unified_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        # Save summary report
        summary_file = f'test_summary_{timestamp}.txt'
        with open(summary_file, 'w') as f:
            f.write("BHIV HR Platform - Test Summary Report\n")
            f.write("=" * 50 + "\n\n")
            
            summary = self.results['unified_summary']
            f.write(f"Overall Health: {summary['overall_health']}\n")
            f.write(f"Database Status: {summary['database_status']}\n")
            f.write(f"Integration Status: {summary['integration_status']}\n\n")
            
            if summary['critical_issues']:
                f.write("Critical Issues:\n")
                for issue in summary['critical_issues']:
                    f.write(f"- {issue}\n")
                f.write("\n")
            
            if summary['recommendations']:
                f.write("Recommendations:\n")
                for rec in summary['recommendations']:
                    f.write(f"- {rec}\n")
        
        print(f"\nResults saved:")
        print(f"   Detailed: {unified_file}")
        print(f"   Summary: {summary_file}")

def main():
    """Run master test suite"""
    runner = MasterTestRunner()
    runner.run_all_tests()

if __name__ == "__main__":
    main()
