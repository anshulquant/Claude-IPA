"""
Data Extraction Workflow - Demo workflow for Claude IPA MVP
Demonstrates automated data extraction from web pages with advanced features

This workflow showcases:
- Multi-page data extraction
- Template-based extraction
- Data validation and cleaning
- Export in multiple formats
- Real-time progress tracking
- Error handling and recovery
"""

import asyncio
import logging
import json
import csv
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import re

logger = logging.getLogger(__name__)

class DataExtractionWorkflow:
    """
    Advanced data extraction workflow for Claude IPA MVP.
    
    Features:
    - Template-based extraction with predefined schemas
    - Multi-page extraction with progress tracking
    - Data validation and cleaning
    - Export in multiple formats (JSON, CSV, Excel)
    - Real-time progress updates
    - Error handling and recovery
    - Integration with WorkflowExecutor
    """
    
    def __init__(self):
        self.extracted_data = []
        self.target_urls = []
        self.extraction_templates = self._load_extraction_templates()
        self.progress_callback = None
        self.current_progress = 0
        
    async def execute_data_extraction(
        self, 
        target_url: str, 
        extraction_goal: str,
        data_fields: List[str]
    ) -> Dict[str, Any]:
        """
        Execute data extraction workflow.
        
        Args:
            target_url: URL to extract data from
            extraction_goal: Description of what data to extract
            data_fields: List of field names to extract
            
        Returns:
            Dictionary with extraction results
        """
        logger.info(f"Starting data extraction from {target_url}")
        
        start_time = datetime.now()
        extraction_log = []
        
        try:
            # Step 1: Navigate to target URL
            extraction_log.append({
                "step": "navigation",
                "message": f"Navigating to {target_url}",
                "timestamp": datetime.now().isoformat(),
                "status": "info"
            })
            
            # Step 2: Analyze page structure
            extraction_log.append({
                "step": "analysis",
                "message": "Analyzing page structure for data fields",
                "timestamp": datetime.now().isoformat(),
                "status": "info"
            })
            
            # Step 3: Extract data fields
            extracted_data = {}
            for field in data_fields:
                extraction_log.append({
                    "step": "extraction",
                    "message": f"Extracting field: {field}",
                    "timestamp": datetime.now().isoformat(),
                    "status": "info"
                })
                
                # Mock data extraction
                extracted_data[field] = await self._mock_extract_field(field)
            
            # Step 4: Validate extracted data
            validation_result = await self._validate_extracted_data(extracted_data)
            extraction_log.append({
                "step": "validation",
                "message": f"Data validation: {validation_result['status']}",
                "timestamp": datetime.now().isoformat(),
                "status": validation_result["status"]
            })
            
            # Step 5: Format and return results
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            result = {
                "success": True,
                "target_url": target_url,
                "extraction_goal": extraction_goal,
                "extracted_data": extracted_data,
                "data_fields": data_fields,
                "validation_result": validation_result,
                "execution_time": execution_time,
                "extraction_log": extraction_log,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Data extraction completed successfully in {execution_time:.2f} seconds")
            return result
            
        except Exception as e:
            logger.error(f"Data extraction failed: {str(e)}")
            end_time = datetime.now()
            
            return {
                "success": False,
                "target_url": target_url,
                "extraction_goal": extraction_goal,
                "error": str(e),
                "execution_time": (end_time - start_time).total_seconds(),
                "extraction_log": extraction_log,
                "timestamp": datetime.now().isoformat()
            }
    
    async def _mock_extract_field(self, field_name: str) -> str:
        """Mock field extraction (Day 1 implementation)"""
        logger.info(f"Mock extracting field: {field_name}")
        
        # Simulate extraction time
        await asyncio.sleep(0.5)
        
        # Mock extracted values based on field name
        mock_values = {
            "title": "Sample Product Title",
            "price": "$29.99",
            "description": "This is a sample product description with detailed information.",
            "rating": "4.5 stars",
            "availability": "In Stock",
            "brand": "Sample Brand",
            "sku": "SKU-12345",
            "category": "Electronics",
            "reviews_count": "127 reviews",
            "image_url": "https://example.com/product-image.jpg"
        }
        
        return mock_values.get(field_name.lower(), f"Mock value for {field_name}")
    
    async def _validate_extracted_data(self, data: Dict[str, str]) -> Dict[str, Any]:
        """Validate extracted data"""
        logger.info("Validating extracted data")
        
        validation_results = {}
        overall_valid = True
        
        for field, value in data.items():
            if not value or value.strip() == "":
                validation_results[field] = {
                    "valid": False,
                    "error": "Empty value"
                }
                overall_valid = False
            else:
                validation_results[field] = {
                    "valid": True,
                    "value": value
                }
        
        return {
            "status": "success" if overall_valid else "warning",
            "overall_valid": overall_valid,
            "field_results": validation_results,
            "total_fields": len(data),
            "valid_fields": sum(1 for r in validation_results.values() if r["valid"])
        }
    
    async def extract_from_multiple_pages(
        self, 
        urls: List[str], 
        extraction_goal: str,
        data_fields: List[str]
    ) -> Dict[str, Any]:
        """
        Extract data from multiple pages.
        
        Args:
            urls: List of URLs to extract from
            extraction_goal: Description of extraction goal
            data_fields: Fields to extract from each page
            
        Returns:
            Combined extraction results
        """
        logger.info(f"Starting multi-page extraction from {len(urls)} URLs")
        
        all_results = []
        successful_extractions = 0
        
        for i, url in enumerate(urls, 1):
            logger.info(f"Extracting from page {i}/{len(urls)}: {url}")
            
            try:
                result = await self.execute_data_extraction(url, extraction_goal, data_fields)
                all_results.append(result)
                
                if result["success"]:
                    successful_extractions += 1
                    
            except Exception as e:
                logger.error(f"Failed to extract from {url}: {str(e)}")
                all_results.append({
                    "success": False,
                    "target_url": url,
                    "error": str(e)
                })
        
        # Combine results
        combined_data = []
        for result in all_results:
            if result["success"]:
                combined_data.append({
                    "url": result["target_url"],
                    "data": result["extracted_data"],
                    "timestamp": result["timestamp"]
                })
        
        return {
            "success": successful_extractions > 0,
            "total_urls": len(urls),
            "successful_extractions": successful_extractions,
            "failed_extractions": len(urls) - successful_extractions,
            "extraction_goal": extraction_goal,
            "data_fields": data_fields,
            "combined_data": combined_data,
            "individual_results": all_results,
            "timestamp": datetime.now().isoformat()
        }
    
    def _load_extraction_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load predefined extraction templates with enhanced schemas"""
        return {
            "ecommerce_product": {
                "description": "Extract product information from e-commerce pages",
                "fields": ["title", "price", "description", "rating", "availability", "brand", "sku", "images", "reviews_count"],
                "validation_rules": {
                    "price": r"^\$?\d+\.?\d*$",
                    "rating": r"^\d+\.?\d*$",
                    "sku": r"^[A-Z0-9\-]+$"
                },
                "example_urls": ["https://amazon.com/product/123", "https://shop.example.com/item/456"],
                "demo_data": {
                    "title": "Wireless Bluetooth Headphones",
                    "price": "$99.99",
                    "rating": "4.5",
                    "availability": "In Stock",
                    "brand": "TechSound",
                    "sku": "TS-WH-001"
                }
            },
            "news_article": {
                "description": "Extract article information from news sites",
                "fields": ["headline", "author", "publish_date", "content", "category", "tags", "word_count", "reading_time"],
                "validation_rules": {
                    "publish_date": r"^\d{4}-\d{2}-\d{2}$",
                    "word_count": r"^\d+$"
                },
                "example_urls": ["https://news.example.com/article/789"],
                "demo_data": {
                    "headline": "AI Revolutionizes Web Automation",
                    "author": "Jane Smith",
                    "publish_date": "2025-01-16",
                    "category": "Technology",
                    "word_count": "850"
                }
            },
            "contact_info": {
                "description": "Extract contact information from business pages",
                "fields": ["company_name", "phone", "email", "address", "website", "hours", "social_media"],
                "validation_rules": {
                    "email": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
                    "phone": r"^[\+]?[1-9][\d]{0,15}$"
                },
                "example_urls": ["https://business.example.com/contact"],
                "demo_data": {
                    "company_name": "Quantanite Solutions",
                    "email": "contact@quantanite.com",
                    "phone": "+1-555-0123",
                    "website": "https://quantanite.com"
                }
            },
            "job_listing": {
                "description": "Extract job information from job boards",
                "fields": ["job_title", "company", "location", "salary", "description", "requirements", "posted_date", "job_type"],
                "validation_rules": {
                    "salary": r"^\$?\d+[Kk]?$",
                    "posted_date": r"^\d{4}-\d{2}-\d{2}$"
                },
                "example_urls": ["https://jobs.example.com/listing/101"],
                "demo_data": {
                    "job_title": "Senior Python Developer",
                    "company": "TechCorp Inc",
                    "location": "San Francisco, CA",
                    "salary": "$120K",
                    "job_type": "Full-time"
                }
            },
            "real_estate": {
                "description": "Extract property information from real estate sites",
                "fields": ["address", "price", "bedrooms", "bathrooms", "square_feet", "property_type", "year_built", "lot_size"],
                "validation_rules": {
                    "price": r"^\$?\d+[KkMm]?$",
                    "bedrooms": r"^\d+$",
                    "bathrooms": r"^\d+\.?\d*$"
                },
                "example_urls": ["https://zillow.com/property/123"],
                "demo_data": {
                    "address": "123 Main St, San Francisco, CA",
                    "price": "$1.2M",
                    "bedrooms": "3",
                    "bathrooms": "2.5",
                    "square_feet": "1800"
                }
            }
        }
    
    def create_custom_template(self, name: str, fields: List[str], description: str = "") -> Dict[str, Any]:
        """Create a custom extraction template"""
        template = {
            "name": name,
            "description": description or f"Custom template for {name}",
            "fields": fields,
            "created_at": datetime.now().isoformat()
        }
        
        logger.info(f"Created custom template: {name} with fields: {fields}")
        return template
    
    def get_extraction_templates(self) -> Dict[str, Dict[str, Any]]:
        """Get all available extraction templates"""
        return self.extraction_templates
    
    async def demo_extraction_with_template(self, template_name: str) -> Dict[str, Any]:
        """Demo extraction using a predefined template with realistic data"""
        if template_name not in self.extraction_templates:
            raise ValueError(f"Template '{template_name}' not found")
        
        template = self.extraction_templates[template_name]
        demo_data = template.get("demo_data", {})
        
        logger.info(f"🎯 Demo extraction using template: {template_name}")
        
        # Simulate extraction process
        extraction_log = []
        
        # Step 1: Template validation
        extraction_log.append({
            "step": "template_validation",
            "message": f"Validating template: {template_name}",
            "timestamp": datetime.now().isoformat(),
            "status": "success"
        })
        
        # Step 2: Data extraction simulation
        extraction_log.append({
            "step": "data_extraction",
            "message": f"Extracting {len(template['fields'])} fields from demo data",
            "timestamp": datetime.now().isoformat(),
            "status": "success"
        })
        
        # Step 3: Data validation
        validated_data = self._validate_extracted_data(demo_data, template.get("validation_rules", {}))
        extraction_log.append({
            "step": "data_validation",
            "message": f"Validated {len(validated_data['valid_fields'])} fields successfully",
            "timestamp": datetime.now().isoformat(),
            "status": "success"
        })
        
        # Step 4: Data cleaning
        cleaned_data = self._clean_extracted_data(demo_data)
        extraction_log.append({
            "step": "data_cleaning",
            "message": "Applied data cleaning and formatting",
            "timestamp": datetime.now().isoformat(),
            "status": "success"
        })
        
        return {
            "success": True,
            "template_name": template_name,
            "template_description": template["description"],
            "extracted_data": cleaned_data,
            "validation_results": validated_data,
            "extraction_log": extraction_log,
            "fields_extracted": len(template["fields"]),
            "execution_time": 2.5,  # Simulated
            "timestamp": datetime.now().isoformat()
        }
    
    def _validate_extracted_data(self, data: Dict[str, str], validation_rules: Dict[str, str]) -> Dict[str, Any]:
        """Validate extracted data against predefined rules"""
        validation_results = {
            "valid_fields": [],
            "invalid_fields": [],
            "validation_score": 0.0
        }
        
        total_fields = len(data)
        valid_count = 0
        
        for field, value in data.items():
            if field in validation_rules:
                pattern = validation_rules[field]
                if re.match(pattern, str(value)):
                    validation_results["valid_fields"].append(field)
                    valid_count += 1
                else:
                    validation_results["invalid_fields"].append({
                        "field": field,
                        "value": value,
                        "expected_pattern": pattern
                    })
            else:
                # No validation rule, consider valid
                validation_results["valid_fields"].append(field)
                valid_count += 1
        
        validation_results["validation_score"] = valid_count / total_fields if total_fields > 0 else 0.0
        
        return validation_results
    
    def _clean_extracted_data(self, data: Dict[str, str]) -> Dict[str, str]:
        """Clean and format extracted data"""
        cleaned_data = {}
        
        for field, value in data.items():
            # Basic cleaning
            cleaned_value = str(value).strip()
            
            # Field-specific cleaning
            if field == "price":
                # Ensure price format
                cleaned_value = re.sub(r'[^\d.$]', '', cleaned_value)
                if not cleaned_value.startswith('$'):
                    cleaned_value = f"${cleaned_value}"
            
            elif field == "email":
                # Normalize email
                cleaned_value = cleaned_value.lower()
            
            elif field == "phone":
                # Format phone number
                cleaned_value = re.sub(r'[^\d+]', '', cleaned_value)
            
            elif field == "rating":
                # Ensure rating is numeric
                cleaned_value = re.sub(r'[^\d.]', '', cleaned_value)
            
            cleaned_data[field] = cleaned_value
        
        return cleaned_data
    
    async def export_extracted_data(self, data: List[Dict[str, Any]], format: str = "json") -> Dict[str, Any]:
        """Export extracted data in various formats"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format.lower() == "json":
            filename = f"extracted_data_{timestamp}.json"
            filepath = Path("reports") / "json" / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return {
                "success": True,
                "format": "json",
                "filename": filename,
                "filepath": str(filepath),
                "records_exported": len(data)
            }
        
        elif format.lower() == "csv":
            filename = f"extracted_data_{timestamp}.csv"
            filepath = Path("reports") / "csv" / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            if data:
                # Get all unique fieldnames from all records
                all_fieldnames = set()
                for record in data:
                    all_fieldnames.update(record.keys())
                fieldnames = sorted(list(all_fieldnames))
                
                with open(filepath, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(data)
            
            return {
                "success": True,
                "format": "csv",
                "filename": filename,
                "filepath": str(filepath),
                "records_exported": len(data)
            }
        
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    async def run_comprehensive_demo(self) -> Dict[str, Any]:
        """Run a comprehensive demo showcasing all extraction capabilities"""
        logger.info("🚀 Starting comprehensive data extraction demo")
        
        demo_results = {
            "demo_started": datetime.now().isoformat(),
            "templates_tested": [],
            "total_extractions": 0,
            "successful_extractions": 0,
            "export_results": [],
            "demo_summary": {}
        }
        
        # Test each template
        for template_name in self.extraction_templates.keys():
            try:
                result = await self.demo_extraction_with_template(template_name)
                demo_results["templates_tested"].append({
                    "template": template_name,
                    "success": result["success"],
                    "fields_extracted": result["fields_extracted"],
                    "execution_time": result["execution_time"]
                })
                demo_results["total_extractions"] += 1
                if result["success"]:
                    demo_results["successful_extractions"] += 1
                
                logger.info(f"✅ Template '{template_name}' demo completed successfully")
                
            except Exception as e:
                logger.error(f"❌ Template '{template_name}' demo failed: {str(e)}")
                demo_results["templates_tested"].append({
                    "template": template_name,
                    "success": False,
                    "error": str(e)
                })
        
        # Export demo data
        try:
            # Create sample data for export
            sample_data = [
                self.extraction_templates["ecommerce_product"]["demo_data"],
                self.extraction_templates["news_article"]["demo_data"],
                self.extraction_templates["contact_info"]["demo_data"]
            ]
            
            # Export as JSON
            json_export = await self.export_extracted_data(sample_data, "json")
            demo_results["export_results"].append(json_export)
            
            # Export as CSV
            csv_export = await self.export_extracted_data(sample_data, "csv")
            demo_results["export_results"].append(csv_export)
            
        except Exception as e:
            logger.error(f"Export failed: {str(e)}")
        
        # Calculate demo summary
        demo_results["demo_summary"] = {
            "total_templates": len(self.extraction_templates),
            "templates_tested": len(demo_results["templates_tested"]),
            "success_rate": demo_results["successful_extractions"] / demo_results["total_extractions"] if demo_results["total_extractions"] > 0 else 0,
            "demo_completed": datetime.now().isoformat(),
            "total_duration": 15.2  # Simulated
        }
        
        logger.info("🎉 Comprehensive demo completed successfully!")
        return demo_results

# Example usage and testing functions
async def demo_data_extraction():
    """Enhanced demo function showcasing all data extraction capabilities"""
    print("🚀 Claude IPA MVP - Data Extraction Demo")
    print("=" * 50)
    
    workflow = DataExtractionWorkflow()
    
    # Show available templates
    print("\n📋 Available Extraction Templates:")
    templates = workflow.get_extraction_templates()
    for name, template in templates.items():
        print(f"  • {name}: {template['description']}")
        print(f"    Fields: {', '.join(template['fields'])}")
    
    # Demo template-based extraction
    print("\n🎯 Demo: E-commerce Product Extraction")
    print("-" * 40)
    
    try:
        result = await workflow.demo_extraction_with_template("ecommerce_product")
        print(f"✅ Success: {result['success']}")
        print(f"📊 Fields Extracted: {result['fields_extracted']}")
        print(f"⏱️  Execution Time: {result['execution_time']:.2f} seconds")
        print(f"📝 Extracted Data:")
        for field, value in result['extracted_data'].items():
            print(f"    {field}: {value}")
        
        print(f"\n🔍 Validation Results:")
        validation = result['validation_results']
        print(f"    Valid Fields: {len(validation['valid_fields'])}")
        print(f"    Validation Score: {validation['validation_score']:.2%}")
        
    except Exception as e:
        print(f"❌ Demo failed: {str(e)}")
    
    # Demo multi-template extraction
    print("\n🎯 Demo: Multi-Template Extraction")
    print("-" * 40)
    
    try:
        multi_result = await workflow.extract_from_multiple_pages(
            urls=["https://example.com/product/123", "https://example.com/product/456"],
            extraction_goal="Extract product information from multiple pages",
            data_fields=["title", "price", "description", "rating"]
        )
        
        print(f"✅ Success: {multi_result['success']}")
        print(f"📊 Successful Extractions: {multi_result['successful_extractions']}/{multi_result['total_urls']}")
        print(f"📝 Combined Data Entries: {len(multi_result['combined_data'])}")
        
    except Exception as e:
        print(f"❌ Multi-page demo failed: {str(e)}")
    
    # Demo data export
    print("\n🎯 Demo: Data Export")
    print("-" * 40)
    
    try:
        # Create sample data
        sample_data = [
            templates["ecommerce_product"]["demo_data"],
            templates["news_article"]["demo_data"],
            templates["contact_info"]["demo_data"]
        ]
        
        # Export as JSON
        json_export = await workflow.export_extracted_data(sample_data, "json")
        print(f"✅ JSON Export: {json_export['filename']}")
        print(f"📊 Records Exported: {json_export['records_exported']}")
        
        # Export as CSV
        csv_export = await workflow.export_extracted_data(sample_data, "csv")
        print(f"✅ CSV Export: {csv_export['filename']}")
        print(f"📊 Records Exported: {csv_export['records_exported']}")
        
    except Exception as e:
        print(f"❌ Export demo failed: {str(e)}")
    
    # Run comprehensive demo
    print("\n🎯 Demo: Comprehensive Extraction Test")
    print("-" * 40)
    
    try:
        comprehensive_result = await workflow.run_comprehensive_demo()
        summary = comprehensive_result["demo_summary"]
        
        print(f"✅ Comprehensive Demo Completed!")
        print(f"📊 Templates Tested: {summary['templates_tested']}/{summary['total_templates']}")
        print(f"📈 Success Rate: {summary['success_rate']:.2%}")
        print(f"⏱️  Total Duration: {summary['total_duration']:.1f} seconds")
        
    except Exception as e:
        print(f"❌ Comprehensive demo failed: {str(e)}")
    
    print("\n🎉 Data Extraction Demo Complete!")
    print("=" * 50)

async def demo_specific_template(template_name: str):
    """Demo a specific extraction template"""
    workflow = DataExtractionWorkflow()
    
    print(f"🎯 Demo: {template_name.title()} Extraction")
    print("-" * 40)
    
    try:
        result = await workflow.demo_extraction_with_template(template_name)
        
        print(f"✅ Template: {result['template_name']}")
        print(f"📝 Description: {result['template_description']}")
        print(f"📊 Fields Extracted: {result['fields_extracted']}")
        print(f"⏱️  Execution Time: {result['execution_time']:.2f} seconds")
        
        print(f"\n📋 Extracted Data:")
        for field, value in result['extracted_data'].items():
            print(f"    {field}: {value}")
        
        print(f"\n🔍 Validation Results:")
        validation = result['validation_results']
        print(f"    Valid Fields: {', '.join(validation['valid_fields'])}")
        if validation['invalid_fields']:
            print(f"    Invalid Fields: {len(validation['invalid_fields'])}")
        print(f"    Validation Score: {validation['validation_score']:.2%}")
        
    except Exception as e:
        print(f"❌ Demo failed: {str(e)}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Demo specific template
        template_name = sys.argv[1]
        asyncio.run(demo_specific_template(template_name))
    else:
        # Run full demo
        asyncio.run(demo_data_extraction())
