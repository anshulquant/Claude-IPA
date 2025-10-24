"""
Integration Test Runner

Main script to run all integration tests and generate comprehensive reports.
"""

import asyncio
import logging
import time
import json
import os
from typing import Dict, Any, List
from datetime import datetime

from tests.integration.test_workflow_integration import run_integration_test_suite
from tests.integration.test_component_integration import TestComponentIntegration
from tests.integration.test_performance_integration import TestPerformanceIntegration

logger = logging.getLogger(__name__)


class IntegrationTestRunner:
    """Main integration test runner"""
    
    def __init__(self):
        self.test_results = []
        self.start_time = None
        self.end_time = None
        
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all integration tests"""
        logger.info("Starting comprehensive integration test suite")
        
        self.start_time = time.time()
        
        try:
            # Run workflow integration tests
            workflow_results = await self._run_workflow_tests()
            self.test_results.extend(workflow_results)
            
            # Run component integration tests
            component_results = await self._run_component_tests()
            self.test_results.extend(component_results)
            
            # Run performance integration tests
            performance_results = await self._run_performance_tests()
            self.test_results.extend(performance_results)
            
            # Run end-to-end integration tests
            e2e_results = await self._run_e2e_tests()
            self.test_results.extend(e2e_results)
            
        except Exception as e:
            logger.error(f"Integration test suite failed: {e}")
            self.test_results.append({
                "test_category": "Integration Suite",
                "test_name": "Overall Suite",
                "success": False,
                "error": str(e),
                "timestamp": time.time()
            })
        
        self.end_time = time.time()
        
        # Generate comprehensive report
        report = self._generate_comprehensive_report()
        
        # Save report to file
        self._save_report(report)
        
        return report
    
    async def _run_workflow_tests(self) -> List[Dict[str, Any]]:
        """Run workflow integration tests"""
        logger.info("Running workflow integration tests")
        
        results = []
        
        try:
            # Run the workflow integration test suite
            suite_results = await run_integration_test_suite()
            
            # Process results
            for category_result in suite_results.get("test_results", []):
                results.append({
                    "test_category": "Workflow Integration",
                    "test_name": category_result.get("category", "Unknown"),
                    "success": category_result.get("success", False),
                    "message": category_result.get("message", ""),
                    "error": category_result.get("error", ""),
                    "timestamp": time.time()
                })
            
            logger.info(f"Workflow integration tests completed: {len(results)} tests")
            
        except Exception as e:
            logger.error(f"Workflow integration tests failed: {e}")
            results.append({
                "test_category": "Workflow Integration",
                "test_name": "Workflow Suite",
                "success": False,
                "error": str(e),
                "timestamp": time.time()
            })
        
        return results
    
    async def _run_component_tests(self) -> List[Dict[str, Any]]:
        """Run component integration tests"""
        logger.info("Running component integration tests")
        
        results = []
        
        try:
            # Test component integration
            test_instance = TestComponentIntegration()
            
            # Run individual component tests
            component_tests = [
                "test_workflow_executor_browser_integration",
                "test_workflow_executor_orchestrator_integration",
                "test_workflow_executor_review_queue_integration",
                "test_browser_orchestrator_integration",
                "test_review_queue_workflow_integration",
                "test_error_propagation_integration",
                "test_performance_integration",
                "test_data_flow_integration",
                "test_state_consistency_integration"
            ]
            
            for test_name in component_tests:
                try:
                    # Setup test
                    test_fixture = await test_instance.integration_test()
                    await test_fixture.__aenter__()
                    
                    # Run test
                    test_method = getattr(test_instance, test_name)
                    await test_method(test_fixture)
                    
                    results.append({
                        "test_category": "Component Integration",
                        "test_name": test_name,
                        "success": True,
                        "message": "Test passed",
                        "timestamp": time.time()
                    })
                    
                    # Cleanup
                    await test_fixture.__aexit__(None, None, None)
                    
                except Exception as e:
                    logger.error(f"Component test {test_name} failed: {e}")
                    results.append({
                        "test_category": "Component Integration",
                        "test_name": test_name,
                        "success": False,
                        "error": str(e),
                        "timestamp": time.time()
                    })
            
            logger.info(f"Component integration tests completed: {len(results)} tests")
            
        except Exception as e:
            logger.error(f"Component integration tests failed: {e}")
            results.append({
                "test_category": "Component Integration",
                "test_name": "Component Suite",
                "success": False,
                "error": str(e),
                "timestamp": time.time()
            })
        
        return results
    
    async def _run_performance_tests(self) -> List[Dict[str, Any]]:
        """Run performance integration tests"""
        logger.info("Running performance integration tests")
        
        results = []
        
        try:
            # Test performance integration
            test_instance = TestPerformanceIntegration()
            
            # Run individual performance tests
            performance_tests = [
                "test_single_workflow_performance",
                "test_concurrent_workflow_performance",
                "test_memory_performance",
                "test_browser_controller_performance",
                "test_orchestrator_performance",
                "test_review_queue_performance",
                "test_system_resource_usage",
                "test_scalability_performance",
                "test_stress_performance",
                "test_performance_regression"
            ]
            
            for test_name in performance_tests:
                try:
                    # Setup test
                    test_fixture = await test_instance.perf_test()
                    await test_fixture.__aenter__()
                    
                    # Run test
                    test_method = getattr(test_instance, test_name)
                    await test_method(test_fixture)
                    
                    results.append({
                        "test_category": "Performance Integration",
                        "test_name": test_name,
                        "success": True,
                        "message": "Test passed",
                        "timestamp": time.time()
                    })
                    
                    # Cleanup
                    await test_fixture.__aexit__(None, None, None)
                    
                except Exception as e:
                    logger.error(f"Performance test {test_name} failed: {e}")
                    results.append({
                        "test_category": "Performance Integration",
                        "test_name": test_name,
                        "success": False,
                        "error": str(e),
                        "timestamp": time.time()
                    })
            
            logger.info(f"Performance integration tests completed: {len(results)} tests")
            
        except Exception as e:
            logger.error(f"Performance integration tests failed: {e}")
            results.append({
                "test_category": "Performance Integration",
                "test_name": "Performance Suite",
                "success": False,
                "error": str(e),
                "timestamp": time.time()
            })
        
        return results
    
    async def _run_e2e_tests(self) -> List[Dict[str, Any]]:
        """Run end-to-end integration tests"""
        logger.info("Running end-to-end integration tests")
        
        results = []
        
        try:
            # Import and run E2E tests
            from tests.integration.test_workflow_integration import TestWorkflowScenarios
            
            test_instance = TestWorkflowScenarios()
            
            # Run E2E tests
            e2e_tests = [
                "test_all_workflow_scenarios"
            ]
            
            for test_name in e2e_tests:
                try:
                    # Setup test
                    test_fixture = await test_instance.scenario_test()
                    await test_fixture.__aenter__()
                    
                    # Run test
                    test_method = getattr(test_instance, test_name)
                    await test_method(test_fixture)
                    
                    results.append({
                        "test_category": "End-to-End Integration",
                        "test_name": test_name,
                        "success": True,
                        "message": "Test passed",
                        "timestamp": time.time()
                    })
                    
                    # Cleanup
                    await test_fixture.__aexit__(None, None, None)
                    
                except Exception as e:
                    logger.error(f"E2E test {test_name} failed: {e}")
                    results.append({
                        "test_category": "End-to-End Integration",
                        "test_name": test_name,
                        "success": False,
                        "error": str(e),
                        "timestamp": time.time()
                    })
            
            logger.info(f"End-to-end integration tests completed: {len(results)} tests")
            
        except Exception as e:
            logger.error(f"End-to-end integration tests failed: {e}")
            results.append({
                "test_category": "End-to-End Integration",
                "test_name": "E2E Suite",
                "success": False,
                "error": str(e),
                "timestamp": time.time()
            })
        
        return results
    
    def _generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        total_tests = len(self.test_results)
        successful_tests = sum(1 for r in self.test_results if r.get("success", False))
        failed_tests = total_tests - successful_tests
        
        # Calculate execution time
        execution_time = self.end_time - self.start_time if self.end_time and self.start_time else 0
        
        # Group results by category
        category_stats = {}
        for result in self.test_results:
            category = result.get("test_category", "Unknown")
            if category not in category_stats:
                category_stats[category] = {"total": 0, "successful": 0, "failed": 0}
            
            category_stats[category]["total"] += 1
            if result.get("success", False):
                category_stats[category]["successful"] += 1
            else:
                category_stats[category]["failed"] += 1
        
        # Calculate success rates
        for category in category_stats:
            stats = category_stats[category]
            stats["success_rate"] = stats["successful"] / stats["total"] if stats["total"] > 0 else 0
        
        # Overall success rate
        overall_success_rate = successful_tests / total_tests if total_tests > 0 else 0
        
        # Generate report
        report = {
            "test_summary": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "failed_tests": failed_tests,
                "success_rate": overall_success_rate,
                "execution_time_seconds": execution_time,
                "timestamp": datetime.now().isoformat()
            },
            "category_breakdown": category_stats,
            "test_results": self.test_results,
            "recommendations": self._generate_recommendations(category_stats, overall_success_rate)
        }
        
        return report
    
    def _generate_recommendations(self, category_stats: Dict[str, Any], overall_success_rate: float) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        # Overall recommendations
        if overall_success_rate < 0.8:
            recommendations.append("Overall success rate is below 80%. Review failed tests and improve system stability.")
        
        if overall_success_rate < 0.9:
            recommendations.append("Consider implementing additional error handling and recovery mechanisms.")
        
        # Category-specific recommendations
        for category, stats in category_stats.items():
            if stats["success_rate"] < 0.7:
                recommendations.append(f"{category} tests have low success rate ({stats['success_rate']:.1%}). Focus on improving this area.")
            
            if stats["failed"] > 0:
                recommendations.append(f"Investigate {stats['failed']} failed tests in {category} category.")
        
        # Performance recommendations
        if "Performance Integration" in category_stats:
            perf_stats = category_stats["Performance Integration"]
            if perf_stats["success_rate"] < 0.8:
                recommendations.append("Performance tests indicate potential performance issues. Consider optimization.")
        
        # Component recommendations
        if "Component Integration" in category_stats:
            comp_stats = category_stats["Component Integration"]
            if comp_stats["success_rate"] < 0.9:
                recommendations.append("Component integration issues detected. Review component interfaces and dependencies.")
        
        return recommendations
    
    def _save_report(self, report: Dict[str, Any]):
        """Save test report to file"""
        try:
            # Create reports directory if it doesn't exist
            os.makedirs("reports", exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"reports/integration_test_report_{timestamp}.json"
            
            # Save report
            with open(filename, "w") as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"Test report saved to: {filename}")
            
            # Also save a summary
            summary_filename = f"reports/integration_test_summary_{timestamp}.txt"
            with open(summary_filename, "w") as f:
                f.write("Integration Test Report Summary\n")
                f.write("=" * 40 + "\n\n")
                f.write(f"Total Tests: {report['test_summary']['total_tests']}\n")
                f.write(f"Successful: {report['test_summary']['successful_tests']}\n")
                f.write(f"Failed: {report['test_summary']['failed_tests']}\n")
                f.write(f"Success Rate: {report['test_summary']['success_rate']:.1%}\n")
                f.write(f"Execution Time: {report['test_summary']['execution_time_seconds']:.2f}s\n\n")
                
                f.write("Category Breakdown:\n")
                f.write("-" * 20 + "\n")
                for category, stats in report['category_breakdown'].items():
                    f.write(f"{category}: {stats['successful']}/{stats['total']} ({stats['success_rate']:.1%})\n")
                
                f.write("\nRecommendations:\n")
                f.write("-" * 15 + "\n")
                for rec in report['recommendations']:
                    f.write(f"- {rec}\n")
            
            logger.info(f"Test summary saved to: {summary_filename}")
            
        except Exception as e:
            logger.error(f"Failed to save test report: {e}")


async def main():
    """Main function to run integration tests"""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("Starting Integration Test Runner")
    
    # Create and run test runner
    runner = IntegrationTestRunner()
    report = await runner.run_all_tests()
    
    # Print summary
    summary = report["test_summary"]
    print("\n" + "="*60)
    print("INTEGRATION TEST RESULTS")
    print("="*60)
    print(f"Total Tests: {summary['total_tests']}")
    print(f"Successful: {summary['successful_tests']}")
    print(f"Failed: {summary['failed_tests']}")
    print(f"Success Rate: {summary['success_rate']:.1%}")
    print(f"Execution Time: {summary['execution_time_seconds']:.2f}s")
    print("="*60)
    
    # Print category breakdown
    print("\nCategory Breakdown:")
    print("-" * 30)
    for category, stats in report["category_breakdown"].items():
        print(f"{category}: {stats['successful']}/{stats['total']} ({stats['success_rate']:.1%})")
    
    # Print recommendations
    if report["recommendations"]:
        print("\nRecommendations:")
        print("-" * 15)
        for rec in report["recommendations"]:
            print(f"- {rec}")
    
    print("\n" + "="*60)
    
    # Return success/failure
    return summary["success_rate"] >= 0.8


if __name__ == "__main__":
    # Run integration tests
    success = asyncio.run(main())
    exit(0 if success else 1)
