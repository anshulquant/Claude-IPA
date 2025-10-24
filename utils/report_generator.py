"""
Execution Report Generator for Quantanite IPA MVP

This module provides comprehensive report generation capabilities:
- Performance analysis and metrics
- Execution logs and step details
- Review queue analytics
- Error analysis and patterns
- Multiple output formats (HTML, JSON, CSV, PDF)
- Interactive visualizations
"""

import os
import json
import csv
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class ReportFormat(Enum):
    """Supported report formats"""
    HTML = "html"
    JSON = "json"
    CSV = "csv"
    PDF = "pdf"

class ReportType(Enum):
    """Types of reports that can be generated"""
    COMPREHENSIVE = "comprehensive"  # Full detailed report
    PERFORMANCE = "performance"      # Performance metrics only
    EXECUTION_LOG = "execution_log"  # Step-by-step execution
    REVIEW_ANALYTICS = "review_analytics"  # Review queue analysis
    ERROR_ANALYSIS = "error_analysis"      # Error patterns and trends
    SUMMARY = "summary"             # High-level overview

class ReportGenerator:
    """Main report generation class"""
    
    def __init__(self, output_dir: str = "reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Create format-specific subdirectories
        for format_type in ReportFormat:
            (self.output_dir / format_type.value).mkdir(exist_ok=True)
    
    def generate_execution_report(
        self,
        workflow_data: Dict[str, Any],
        report_type: ReportType = ReportType.COMPREHENSIVE,
        format: ReportFormat = ReportFormat.HTML
    ) -> str:
        """
        Generate a comprehensive execution report
        
        Args:
            workflow_data: Workflow execution data
            report_type: Type of report to generate
            format: Output format
            
        Returns:
            Path to generated report file
        """
        try:
            # Prepare report data
            report_data = self._prepare_report_data(workflow_data, report_type)
            
            # Generate report based on format
            if format == ReportFormat.HTML:
                return self._generate_html_report(report_data, report_type)
            elif format == ReportFormat.JSON:
                return self._generate_json_report(report_data, report_type)
            elif format == ReportFormat.CSV:
                return self._generate_csv_report(report_data, report_type)
            elif format == ReportFormat.PDF:
                return self._generate_pdf_report(report_data, report_type)
            else:
                raise ValueError(f"Unsupported format: {format}")
                
        except Exception as e:
            logger.error(f"Failed to generate report: {e}")
            raise
    
    def _prepare_report_data(self, workflow_data: Dict[str, Any], report_type: ReportType) -> Dict[str, Any]:
        """Prepare and structure data for report generation"""
        
        # Base report metadata
        report_metadata = {
            "generated_at": datetime.now().isoformat(),
            "report_type": report_type.value,
            "workflow_id": workflow_data.get("workflow_id", "unknown"),
            "generator_version": "1.0.0"
        }
        
        # Extract workflow information
        workflow_info = {
            "id": workflow_data.get("workflow_id", "unknown"),
            "goal": workflow_data.get("goal", "Unknown goal"),
            "start_url": workflow_data.get("start_url", "https://google.com"),
            "status": workflow_data.get("status", "unknown"),
            "created_at": workflow_data.get("created_at", datetime.now().isoformat()),
            "execution_time": workflow_data.get("execution_time", 0.0),
            "success": workflow_data.get("success", False),
            "actions_taken": workflow_data.get("actions_taken", 0),
            "error_message": workflow_data.get("error_message")
        }
        
        # Extract execution log
        execution_log = workflow_data.get("execution_log", [])
        
        # Extract performance metrics
        performance_metrics = workflow_data.get("performance_metrics", {})
        
        # Extract review items
        review_items = workflow_data.get("review_items", [])
        
        # Calculate additional metrics
        metrics = self._calculate_metrics(execution_log, performance_metrics, review_items)
        
        # Prepare report data based on type
        if report_type == ReportType.COMPREHENSIVE:
            report_data = {
                "metadata": report_metadata,
                "workflow_info": workflow_info,
                "execution_log": execution_log,
                "performance_metrics": performance_metrics,
                "calculated_metrics": metrics,
                "review_items": review_items,
                "error_analysis": self._analyze_errors(execution_log),
                "step_analysis": self._analyze_steps(execution_log),
                "timeline": self._create_timeline(execution_log)
            }
        elif report_type == ReportType.PERFORMANCE:
            report_data = {
                "metadata": report_metadata,
                "workflow_info": workflow_info,
                "performance_metrics": performance_metrics,
                "calculated_metrics": metrics,
                "performance_analysis": self._analyze_performance(execution_log, performance_metrics)
            }
        elif report_type == ReportType.EXECUTION_LOG:
            report_data = {
                "metadata": report_metadata,
                "workflow_info": workflow_info,
                "execution_log": execution_log,
                "step_analysis": self._analyze_steps(execution_log),
                "timeline": self._create_timeline(execution_log)
            }
        elif report_type == ReportType.REVIEW_ANALYTICS:
            report_data = {
                "metadata": report_metadata,
                "workflow_info": workflow_info,
                "review_items": review_items,
                "review_analysis": self._analyze_reviews(review_items),
                "review_patterns": self._analyze_review_patterns(review_items)
            }
        elif report_type == ReportType.ERROR_ANALYSIS:
            report_data = {
                "metadata": report_metadata,
                "workflow_info": workflow_info,
                "execution_log": execution_log,
                "error_analysis": self._analyze_errors(execution_log),
                "error_patterns": self._analyze_error_patterns(execution_log)
            }
        elif report_type == ReportType.SUMMARY:
            report_data = {
                "metadata": report_metadata,
                "workflow_info": workflow_info,
                "summary_metrics": self._create_summary_metrics(workflow_info, metrics),
                "key_insights": self._generate_key_insights(workflow_info, metrics, execution_log)
            }
        else:
            raise ValueError(f"Unsupported report type: {report_type}")
        
        return report_data
    
    def _calculate_metrics(self, execution_log: List[Dict], performance_metrics: Dict, review_items: List) -> Dict[str, Any]:
        """Calculate additional metrics from execution data"""
        
        # Step analysis
        total_steps = len(execution_log)
        successful_steps = sum(1 for step in execution_log if step.get("status") == "success")
        failed_steps = sum(1 for step in execution_log if step.get("status") == "error")
        warning_steps = sum(1 for step in execution_log if step.get("status") == "warning")
        
        # Time analysis
        if execution_log:
            start_time = datetime.fromisoformat(execution_log[0]["timestamp"])
            end_time = datetime.fromisoformat(execution_log[-1]["timestamp"])
            total_duration = (end_time - start_time).total_seconds()
        else:
            total_duration = 0.0
        
        # Action type analysis
        action_types = {}
        for step in execution_log:
            action = step.get("step", "").split(":")[0] if ":" in step.get("step", "") else step.get("step", "unknown")
            action_types[action] = action_types.get(action, 0) + 1
        
        # Review analysis
        total_reviews = len(review_items)
        pending_reviews = sum(1 for item in review_items if item.get("status") == "pending")
        approved_reviews = sum(1 for item in review_items if item.get("status") == "approved")
        rejected_reviews = sum(1 for item in review_items if item.get("status") == "rejected")
        
        return {
            "total_steps": total_steps,
            "successful_steps": successful_steps,
            "failed_steps": failed_steps,
            "warning_steps": warning_steps,
            "success_rate": (successful_steps / total_steps * 100) if total_steps > 0 else 0,
            "failure_rate": (failed_steps / total_steps * 100) if total_steps > 0 else 0,
            "total_duration": total_duration,
            "average_step_time": total_duration / total_steps if total_steps > 0 else 0,
            "action_types": action_types,
            "total_reviews": total_reviews,
            "pending_reviews": pending_reviews,
            "approved_reviews": approved_reviews,
            "rejected_reviews": rejected_reviews,
            "review_approval_rate": (approved_reviews / total_reviews * 100) if total_reviews > 0 else 0
        }
    
    def _analyze_errors(self, execution_log: List[Dict]) -> Dict[str, Any]:
        """Analyze errors in execution log"""
        error_steps = [step for step in execution_log if step.get("status") == "error"]
        
        error_types = {}
        error_messages = []
        
        for step in error_steps:
            message = step.get("message", "Unknown error")
            error_messages.append(message)
            
            # Categorize error types
            if "timeout" in message.lower():
                error_types["timeout"] = error_types.get("timeout", 0) + 1
            elif "network" in message.lower():
                error_types["network"] = error_types.get("network", 0) + 1
            elif "permission" in message.lower():
                error_types["permission"] = error_types.get("permission", 0) + 1
            elif "browser" in message.lower():
                error_types["browser"] = error_types.get("browser", 0) + 1
            else:
                error_types["other"] = error_types.get("other", 0) + 1
        
        return {
            "total_errors": len(error_steps),
            "error_types": error_types,
            "error_messages": error_messages,
            "error_rate": (len(error_steps) / len(execution_log) * 100) if execution_log else 0
        }
    
    def _analyze_steps(self, execution_log: List[Dict]) -> Dict[str, Any]:
        """Analyze execution steps"""
        step_analysis = {
            "total_steps": len(execution_log),
            "step_breakdown": {},
            "step_timings": [],
            "status_distribution": {}
        }
        
        for i, step in enumerate(execution_log):
            step_name = step.get("step", f"Step {i+1}")
            status = step.get("status", "unknown")
            
            # Step breakdown
            step_analysis["step_breakdown"][step_name] = {
                "status": status,
                "message": step.get("message", ""),
                "timestamp": step.get("timestamp", "")
            }
            
            # Status distribution
            step_analysis["status_distribution"][status] = step_analysis["status_distribution"].get(status, 0) + 1
        
        return step_analysis
    
    def _create_timeline(self, execution_log: List[Dict]) -> List[Dict[str, Any]]:
        """Create timeline of execution events"""
        timeline = []
        
        for i, step in enumerate(execution_log):
            timeline.append({
                "step_number": i + 1,
                "timestamp": step.get("timestamp", ""),
                "step": step.get("step", f"Step {i+1}"),
                "status": step.get("status", "unknown"),
                "message": step.get("message", ""),
                "duration": 0  # Could be calculated if we had step timings
            })
        
        return timeline
    
    def _analyze_performance(self, execution_log: List[Dict], performance_metrics: Dict) -> Dict[str, Any]:
        """Analyze performance metrics"""
        return {
            "execution_time": performance_metrics.get("total_execution_time", 0),
            "average_step_time": performance_metrics.get("average_step_time", 0),
            "retry_count": performance_metrics.get("retry_count", 0),
            "error_count": performance_metrics.get("error_count", 0),
            "success_rate": performance_metrics.get("success_rate", 0),
            "performance_grade": self._calculate_performance_grade(performance_metrics)
        }
    
    def _calculate_performance_grade(self, performance_metrics: Dict) -> str:
        """Calculate performance grade (A-F)"""
        success_rate = performance_metrics.get("success_rate", 0)
        error_count = performance_metrics.get("error_count", 0)
        
        if success_rate >= 0.95 and error_count == 0:
            return "A"
        elif success_rate >= 0.9 and error_count <= 1:
            return "B"
        elif success_rate >= 0.8 and error_count <= 2:
            return "C"
        elif success_rate >= 0.7 and error_count <= 3:
            return "D"
        else:
            return "F"
    
    def _analyze_reviews(self, review_items: List) -> Dict[str, Any]:
        """Analyze review queue data"""
        if not review_items:
            return {"total_reviews": 0, "analysis": "No reviews found"}
        
        # Review status analysis
        status_counts = {}
        priority_counts = {}
        category_counts = {}
        
        for item in review_items:
            status = item.get("status", "unknown")
            priority = item.get("priority", "unknown")
            category = item.get("category", "unknown")
            
            status_counts[status] = status_counts.get(status, 0) + 1
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
            category_counts[category] = category_counts.get(category, 0) + 1
        
        return {
            "total_reviews": len(review_items),
            "status_distribution": status_counts,
            "priority_distribution": priority_counts,
            "category_distribution": category_counts,
            "average_review_time": sum(item.get("estimated_review_time", 0) for item in review_items) / len(review_items)
        }
    
    def _analyze_review_patterns(self, review_items: List) -> Dict[str, Any]:
        """Analyze patterns in review data"""
        if not review_items:
            return {"patterns": "No review data available"}
        
        # Analyze review timing patterns
        review_times = []
        for item in review_items:
            if "created_at" in item and "reviewed_at" in item:
                created = datetime.fromisoformat(item["created_at"])
                reviewed = datetime.fromisoformat(item["reviewed_at"])
                review_time = (reviewed - created).total_seconds() / 60  # minutes
                review_times.append(review_time)
        
        return {
            "average_review_time_minutes": sum(review_times) / len(review_times) if review_times else 0,
            "fastest_review_minutes": min(review_times) if review_times else 0,
            "slowest_review_minutes": max(review_times) if review_times else 0
        }
    
    def _analyze_error_patterns(self, execution_log: List[Dict]) -> Dict[str, Any]:
        """Analyze error patterns and trends"""
        error_steps = [step for step in execution_log if step.get("status") == "error"]
        
        if not error_steps:
            return {"patterns": "No errors found"}
        
        # Error frequency over time
        error_timestamps = []
        for step in error_steps:
            if "timestamp" in step:
                error_timestamps.append(step["timestamp"])
        
        return {
            "error_frequency": len(error_steps),
            "error_timestamps": error_timestamps,
            "consecutive_errors": self._find_consecutive_errors(execution_log)
        }
    
    def _find_consecutive_errors(self, execution_log: List[Dict]) -> int:
        """Find maximum consecutive errors"""
        max_consecutive = 0
        current_consecutive = 0
        
        for step in execution_log:
            if step.get("status") == "error":
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0
        
        return max_consecutive
    
    def _create_summary_metrics(self, workflow_info: Dict, metrics: Dict) -> Dict[str, Any]:
        """Create high-level summary metrics"""
        return {
            "workflow_id": workflow_info.get("id", "unknown"),
            "goal": workflow_info.get("goal", "Unknown"),
            "status": workflow_info.get("status", "unknown"),
            "success": workflow_info.get("success", False),
            "execution_time": workflow_info.get("execution_time", 0),
            "actions_taken": workflow_info.get("actions_taken", 0),
            "success_rate": metrics.get("success_rate", 0),
            "total_steps": metrics.get("total_steps", 0),
            "total_reviews": metrics.get("total_reviews", 0),
            "performance_grade": self._calculate_performance_grade({"success_rate": metrics.get("success_rate", 0), "error_count": metrics.get("failed_steps", 0)})
        }
    
    def _generate_key_insights(self, workflow_info: Dict, metrics: Dict, execution_log: List[Dict]) -> List[str]:
        """Generate key insights from the data"""
        insights = []
        
        # Success insights
        if workflow_info.get("success", False):
            insights.append("✅ Workflow completed successfully")
        else:
            insights.append("❌ Workflow failed to complete")
        
        # Performance insights
        success_rate = metrics.get("success_rate", 0)
        if success_rate >= 90:
            insights.append("🚀 Excellent performance with high success rate")
        elif success_rate >= 70:
            insights.append("⚠️ Moderate performance, some issues encountered")
        else:
            insights.append("🔴 Poor performance, significant issues detected")
        
        # Review insights
        total_reviews = metrics.get("total_reviews", 0)
        if total_reviews > 0:
            review_approval_rate = metrics.get("review_approval_rate", 0)
            if review_approval_rate >= 80:
                insights.append("👥 High human approval rate for review items")
            else:
                insights.append("👥 Low human approval rate, may need review process improvement")
        
        # Error insights
        failed_steps = metrics.get("failed_steps", 0)
        if failed_steps == 0:
            insights.append("🎯 No errors encountered during execution")
        elif failed_steps <= 2:
            insights.append("⚠️ Few errors encountered, workflow mostly successful")
        else:
            insights.append("🔴 Multiple errors encountered, workflow needs improvement")
        
        # Time insights
        execution_time = workflow_info.get("execution_time", 0)
        if execution_time < 60:
            insights.append("⚡ Fast execution completed in under 1 minute")
        elif execution_time < 300:
            insights.append("⏱️ Moderate execution time")
        else:
            insights.append("🐌 Slow execution, consider optimization")
        
        return insights
    
    def _generate_html_report(self, report_data: Dict[str, Any], report_type: ReportType) -> str:
        """Generate HTML report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        workflow_id = report_data.get("workflow_info", {}).get("id", "unknown")
        filename = f"report_{workflow_id}_{report_type.value}_{timestamp}.html"
        filepath = self.output_dir / "html" / filename
        
        # Generate HTML content
        html_content = self._create_html_content(report_data, report_type)
        
        # Write to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"HTML report generated: {filepath}")
        return str(filepath)
    
    def _create_html_content(self, report_data: Dict[str, Any], report_type: ReportType) -> str:
        """Create HTML content for the report"""
        workflow_info = report_data.get("workflow_info", {})
        metadata = report_data.get("metadata", {})
        
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Quantanite IPA - {report_type.value.title()} Report</title>
    <style>
        {self._get_html_styles()}
    </style>
</head>
<body>
    <div class="container">
        <header class="report-header">
            <h1>🚀 Quantanite IPA Execution Report</h1>
            <div class="report-meta">
                <span class="report-type">{report_type.value.title()} Report</span>
                <span class="generated-at">Generated: {metadata.get('generated_at', 'Unknown')}</span>
            </div>
        </header>
        
        <div class="workflow-info">
            <h2>📋 Workflow Information</h2>
            <div class="info-grid">
                <div class="info-item">
                    <label>Workflow ID:</label>
                    <span>{workflow_info.get('id', 'Unknown')}</span>
                </div>
                <div class="info-item">
                    <label>Goal:</label>
                    <span>{workflow_info.get('goal', 'Unknown')}</span>
                </div>
                <div class="info-item">
                    <label>Status:</label>
                    <span class="status {workflow_info.get('status', 'unknown').lower()}">{workflow_info.get('status', 'Unknown')}</span>
                </div>
                <div class="info-item">
                    <label>Success:</label>
                    <span class="success {'yes' if workflow_info.get('success') else 'no'}">{'Yes' if workflow_info.get('success') else 'No'}</span>
                </div>
                <div class="info-item">
                    <label>Execution Time:</label>
                    <span>{workflow_info.get('execution_time', 0):.2f} seconds</span>
                </div>
                <div class="info-item">
                    <label>Actions Taken:</label>
                    <span>{workflow_info.get('actions_taken', 0)}</span>
                </div>
            </div>
        </div>
        
        {self._generate_html_sections(report_data, report_type)}
        
        <footer class="report-footer">
            <p>Generated by Quantanite IPA Report Generator v{metadata.get('generator_version', '1.0.0')}</p>
        </footer>
    </div>
</body>
</html>
        """
        
        return html
    
    def _get_html_styles(self) -> str:
        """Get CSS styles for HTML reports"""
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 12px;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
            margin-top: 20px;
            margin-bottom: 20px;
        }
        
        .report-header {
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #e5e7eb;
        }
        
        .report-header h1 {
            color: #1f2937;
            font-size: 2.5rem;
            margin-bottom: 10px;
        }
        
        .report-meta {
            display: flex;
            justify-content: center;
            gap: 20px;
            color: #6b7280;
        }
        
        .report-type {
            background: #3b82f6;
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.9rem;
        }
        
        .workflow-info {
            margin-bottom: 30px;
        }
        
        .workflow-info h2 {
            color: #1f2937;
            margin-bottom: 15px;
            font-size: 1.5rem;
        }
        
        .info-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 15px;
        }
        
        .info-item {
            display: flex;
            justify-content: space-between;
            padding: 12px;
            background: #f9fafb;
            border-radius: 8px;
            border-left: 4px solid #3b82f6;
        }
        
        .info-item label {
            font-weight: 600;
            color: #374151;
        }
        
        .status.completed {
            color: #059669;
            font-weight: 600;
        }
        
        .status.failed {
            color: #dc2626;
            font-weight: 600;
        }
        
        .status.running {
            color: #d97706;
            font-weight: 600;
        }
        
        .success.yes {
            color: #059669;
            font-weight: 600;
        }
        
        .success.no {
            color: #dc2626;
            font-weight: 600;
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        
        .metric-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
        }
        
        .metric-value {
            font-size: 2rem;
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .metric-label {
            font-size: 0.9rem;
            opacity: 0.9;
        }
        
        .section {
            margin-bottom: 30px;
        }
        
        .section h2 {
            color: #1f2937;
            margin-bottom: 15px;
            font-size: 1.5rem;
            border-bottom: 2px solid #e5e7eb;
            padding-bottom: 5px;
        }
        
        .execution-log {
            background: #f9fafb;
            border-radius: 8px;
            padding: 20px;
        }
        
        .log-entry {
            display: flex;
            align-items: center;
            padding: 10px;
            margin-bottom: 8px;
            border-radius: 6px;
            border-left: 4px solid #e5e7eb;
        }
        
        .log-entry.success {
            background: #f0fdf4;
            border-left-color: #22c55e;
        }
        
        .log-entry.error {
            background: #fef2f2;
            border-left-color: #ef4444;
        }
        
        .log-entry.warning {
            background: #fffbeb;
            border-left-color: #f59e0b;
        }
        
        .log-entry.info {
            background: #eff6ff;
            border-left-color: #3b82f6;
        }
        
        .log-timestamp {
            font-size: 0.8rem;
            color: #6b7280;
            margin-right: 15px;
            min-width: 120px;
        }
        
        .log-status {
            font-weight: 600;
            margin-right: 15px;
            min-width: 80px;
        }
        
        .log-message {
            flex: 1;
        }
        
        .insights-list {
            list-style: none;
        }
        
        .insights-list li {
            padding: 10px;
            margin-bottom: 8px;
            background: #f9fafb;
            border-radius: 6px;
            border-left: 4px solid #3b82f6;
        }
        
        .report-footer {
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e5e7eb;
            color: #6b7280;
        }
        
        @media (max-width: 768px) {
            .container {
                margin: 10px;
                padding: 15px;
            }
            
            .info-grid {
                grid-template-columns: 1fr;
            }
            
            .metrics-grid {
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            }
        }
        """
    
    def _generate_html_sections(self, report_data: Dict[str, Any], report_type: ReportType) -> str:
        """Generate HTML sections based on report type"""
        sections = []
        
        if report_type == ReportType.COMPREHENSIVE:
            sections.append(self._generate_metrics_section(report_data))
            sections.append(self._generate_execution_log_section(report_data))
            sections.append(self._generate_error_analysis_section(report_data))
            sections.append(self._generate_review_analysis_section(report_data))
        elif report_type == ReportType.PERFORMANCE:
            sections.append(self._generate_metrics_section(report_data))
            sections.append(self._generate_performance_analysis_section(report_data))
        elif report_type == ReportType.EXECUTION_LOG:
            sections.append(self._generate_execution_log_section(report_data))
            sections.append(self._generate_step_analysis_section(report_data))
        elif report_type == ReportType.REVIEW_ANALYTICS:
            sections.append(self._generate_review_analysis_section(report_data))
            sections.append(self._generate_review_patterns_section(report_data))
        elif report_type == ReportType.ERROR_ANALYSIS:
            sections.append(self._generate_error_analysis_section(report_data))
            sections.append(self._generate_error_patterns_section(report_data))
        elif report_type == ReportType.SUMMARY:
            sections.append(self._generate_summary_metrics_section(report_data))
            sections.append(self._generate_key_insights_section(report_data))
        
        return "\n".join(sections)
    
    def _generate_metrics_section(self, report_data: Dict[str, Any]) -> str:
        """Generate metrics section HTML"""
        metrics = report_data.get("calculated_metrics", {})
        
        return f"""
        <div class="section">
            <h2>📊 Performance Metrics</h2>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-value">{metrics.get('success_rate', 0):.1f}%</div>
                    <div class="metric-label">Success Rate</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{metrics.get('total_steps', 0)}</div>
                    <div class="metric-label">Total Steps</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{metrics.get('total_duration', 0):.1f}s</div>
                    <div class="metric-label">Total Duration</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{metrics.get('total_reviews', 0)}</div>
                    <div class="metric-label">Review Items</div>
                </div>
            </div>
        </div>
        """
    
    def _generate_execution_log_section(self, report_data: Dict[str, Any]) -> str:
        """Generate execution log section HTML"""
        execution_log = report_data.get("execution_log", [])
        
        log_entries = ""
        for entry in execution_log:
            status = entry.get("status", "info")
            timestamp = entry.get("timestamp", "")
            step = entry.get("step", "")
            message = entry.get("message", "")
            
            log_entries += f"""
            <div class="log-entry {status}">
                <div class="log-timestamp">{timestamp}</div>
                <div class="log-status">{status.upper()}</div>
                <div class="log-message">
                    <strong>{step}</strong>: {message}
                </div>
            </div>
            """
        
        return f"""
        <div class="section">
            <h2>📝 Execution Log</h2>
            <div class="execution-log">
                {log_entries}
            </div>
        </div>
        """
    
    def _generate_error_analysis_section(self, report_data: Dict[str, Any]) -> str:
        """Generate error analysis section HTML"""
        error_analysis = report_data.get("error_analysis", {})
        
        error_types_html = ""
        for error_type, count in error_analysis.get("error_types", {}).items():
            error_types_html += f"<li>{error_type.title()}: {count}</li>"
        
        return f"""
        <div class="section">
            <h2>🔍 Error Analysis</h2>
            <div class="info-grid">
                <div class="info-item">
                    <label>Total Errors:</label>
                    <span>{error_analysis.get('total_errors', 0)}</span>
                </div>
                <div class="info-item">
                    <label>Error Rate:</label>
                    <span>{error_analysis.get('error_rate', 0):.1f}%</span>
                </div>
            </div>
            <h3>Error Types:</h3>
            <ul class="insights-list">
                {error_types_html}
            </ul>
        </div>
        """
    
    def _generate_review_analysis_section(self, report_data: Dict[str, Any]) -> str:
        """Generate review analysis section HTML"""
        review_analysis = report_data.get("review_analysis", {})
        
        return f"""
        <div class="section">
            <h2>👥 Review Analysis</h2>
            <div class="info-grid">
                <div class="info-item">
                    <label>Total Reviews:</label>
                    <span>{review_analysis.get('total_reviews', 0)}</span>
                </div>
                <div class="info-item">
                    <label>Average Review Time:</label>
                    <span>{review_analysis.get('average_review_time', 0):.1f} minutes</span>
                </div>
            </div>
        </div>
        """
    
    def _generate_key_insights_section(self, report_data: Dict[str, Any]) -> str:
        """Generate key insights section HTML"""
        insights = report_data.get("key_insights", [])
        
        insights_html = ""
        for insight in insights:
            insights_html += f"<li>{insight}</li>"
        
        return f"""
        <div class="section">
            <h2>💡 Key Insights</h2>
            <ul class="insights-list">
                {insights_html}
            </ul>
        </div>
        """
    
    def _generate_json_report(self, report_data: Dict[str, Any], report_type: ReportType) -> str:
        """Generate JSON report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        workflow_id = report_data.get("workflow_info", {}).get("id", "unknown")
        filename = f"report_{workflow_id}_{report_type.value}_{timestamp}.json"
        filepath = self.output_dir / "json" / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"JSON report generated: {filepath}")
        return str(filepath)
    
    def _generate_csv_report(self, report_data: Dict[str, Any], report_type: ReportType) -> str:
        """Generate CSV report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        workflow_id = report_data.get("workflow_info", {}).get("id", "unknown")
        filename = f"report_{workflow_id}_{report_type.value}_{timestamp}.csv"
        filepath = self.output_dir / "csv" / filename
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow(['Metric', 'Value'])
            
            # Write workflow info
            workflow_info = report_data.get("workflow_info", {})
            for key, value in workflow_info.items():
                writer.writerow([f"workflow_{key}", value])
            
            # Write metrics
            metrics = report_data.get("calculated_metrics", {})
            for key, value in metrics.items():
                writer.writerow([f"metric_{key}", value])
        
        logger.info(f"CSV report generated: {filepath}")
        return str(filepath)
    
    def _generate_pdf_report(self, report_data: Dict[str, Any], report_type: ReportType) -> str:
        """Generate PDF report (placeholder - would require additional dependencies)"""
        # This would require libraries like reportlab or weasyprint
        # For now, we'll create a simple text-based report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        workflow_id = report_data.get("workflow_info", {}).get("id", "unknown")
        filename = f"report_{workflow_id}_{report_type.value}_{timestamp}.txt"
        filepath = self.output_dir / "pdf" / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"Quantanite IPA Execution Report\n")
            f.write(f"Report Type: {report_type.value}\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n")
            f.write("=" * 50 + "\n\n")
            
            # Write workflow info
            workflow_info = report_data.get("workflow_info", {})
            f.write("Workflow Information:\n")
            for key, value in workflow_info.items():
                f.write(f"  {key}: {value}\n")
            
            f.write("\n")
            
            # Write metrics
            metrics = report_data.get("calculated_metrics", {})
            f.write("Performance Metrics:\n")
            for key, value in metrics.items():
                f.write(f"  {key}: {value}\n")
        
        logger.info(f"PDF report generated: {filepath}")
        return str(filepath)
    
    # Placeholder methods for additional sections
    def _generate_performance_analysis_section(self, report_data: Dict[str, Any]) -> str:
        return '<div class="section"><h2>⚡ Performance Analysis</h2><p>Performance analysis details would go here.</p></div>'
    
    def _generate_step_analysis_section(self, report_data: Dict[str, Any]) -> str:
        return '<div class="section"><h2>🔍 Step Analysis</h2><p>Step analysis details would go here.</p></div>'
    
    def _generate_review_patterns_section(self, report_data: Dict[str, Any]) -> str:
        return '<div class="section"><h2>📈 Review Patterns</h2><p>Review patterns analysis would go here.</p></div>'
    
    def _generate_error_patterns_section(self, report_data: Dict[str, Any]) -> str:
        return '<div class="section"><h2>🔍 Error Patterns</h2><p>Error patterns analysis would go here.</p></div>'
    
    def _generate_summary_metrics_section(self, report_data: Dict[str, Any]) -> str:
        return '<div class="section"><h2>📊 Summary Metrics</h2><p>Summary metrics would go here.</p></div>'

# Convenience functions
def generate_execution_report(
    workflow_data: Dict[str, Any],
    output_dir: str = "reports",
    format: ReportFormat = ReportFormat.HTML,
    report_type: ReportType = ReportType.COMPREHENSIVE
) -> str:
    """Generate an execution report with default settings"""
    generator = ReportGenerator(output_dir)
    return generator.generate_execution_report(workflow_data, report_type, format)

def generate_batch_report(
    workflows_data: List[Dict[str, Any]],
    output_dir: str = "reports",
    format: ReportFormat = ReportFormat.HTML
) -> str:
    """Generate a batch report for multiple workflows"""
    generator = ReportGenerator(output_dir)
    
    # Create batch summary
    total_workflows = len(workflows_data)
    successful_workflows = sum(1 for wf in workflows_data if wf.get("success", False))
    failed_workflows = total_workflows - successful_workflows
    total_execution_time = sum(wf.get("execution_time", 0) for wf in workflows_data)
    total_actions = sum(wf.get("actions_taken", 0) for wf in workflows_data)
    
    batch_summary = {
        "total_workflows": total_workflows,
        "successful_workflows": successful_workflows,
        "failed_workflows": failed_workflows,
        "success_rate": (successful_workflows / total_workflows * 100) if total_workflows > 0 else 0,
        "total_execution_time": total_execution_time,
        "average_execution_time": total_execution_time / total_workflows if total_workflows > 0 else 0,
        "total_actions": total_actions,
        "average_actions": total_actions / total_workflows if total_workflows > 0 else 0
    }
    
    # Combine all workflow data
    combined_data = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "report_type": "batch",
            "workflow_count": total_workflows,
            "generator_version": "1.0.0"
        },
        "workflows": workflows_data,
        "batch_summary": batch_summary
    }
    
    return generator.generate_execution_report(combined_data, ReportType.SUMMARY, format)

# Example usage
if __name__ == "__main__":
    # Example workflow data
    sample_workflow = {
        "workflow_id": "test_workflow_001",
        "goal": "Test workflow execution",
        "start_url": "https://google.com",
        "status": "completed",
        "success": True,
        "execution_time": 45.2,
        "actions_taken": 5,
        "execution_log": [
            {
                "timestamp": "2024-01-01T10:00:00",
                "step": "Initialize",
                "message": "Starting workflow",
                "status": "info"
            },
            {
                "timestamp": "2024-01-01T10:00:05",
                "step": "Navigate",
                "message": "Navigated to Google",
                "status": "success"
            }
        ],
        "performance_metrics": {
            "total_execution_time": 45.2,
            "average_step_time": 9.04,
            "success_rate": 0.8,
            "error_count": 1
        },
        "review_items": []
    }
    
    # Generate different types of reports
    generator = ReportGenerator()
    
    # Comprehensive HTML report
    html_report = generator.generate_execution_report(
        sample_workflow, 
        ReportType.COMPREHENSIVE, 
        ReportFormat.HTML
    )
    print(f"HTML report generated: {html_report}")
    
    # Performance JSON report
    json_report = generator.generate_execution_report(
        sample_workflow, 
        ReportType.PERFORMANCE, 
        ReportFormat.JSON
    )
    print(f"JSON report generated: {json_report}")
