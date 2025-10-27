"""
Mock Components for Integration Testing

This module provides mock implementations of Developer 1's components
to enable comprehensive integration testing without actual browser automation.
"""

import asyncio
import random
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class BrowserAction(Enum):
    """Browser action types"""
    CLICK = "click"
    TYPE = "type"
    NAVIGATE = "navigate"
    SCROLL = "scroll"
    WAIT = "wait"
    SCREENSHOT = "screenshot"
    EXTRACT_TEXT = "extract_text"
    EXTRACT_ELEMENTS = "extract_elements"


@dataclass
class BrowserElement:
    """Mock browser element"""
    tag: str
    text: str
    attributes: Dict[str, str]
    xpath: str
    visible: bool = True
    enabled: bool = True


@dataclass
class BrowserState:
    """Current browser state"""
    url: str
    title: str
    elements: List[BrowserElement]
    screenshot_path: Optional[str] = None
    page_loaded: bool = True


class MockBrowserController:
    """
    Mock Browser Controller for integration testing
    
    Simulates browser automation without actual browser interaction.
    Provides realistic behavior patterns and error scenarios.
    """
    
    def __init__(self, error_rate: float = 0.1, delay_range: tuple = (0.1, 0.5)):
        self.error_rate = error_rate
        self.delay_range = delay_range
        self.current_state = BrowserState(
            url="about:blank",
            title="Blank Page",
            elements=[]
        )
        self.action_history = []
        self.screenshot_counter = 0
        
    async def navigate(self, url: str) -> Dict[str, Any]:
        """Navigate to a URL"""
        await self._simulate_delay()
        
        if self._should_fail():
            raise Exception(f"Navigation failed to {url}")
            
        self.current_state.url = url
        self.current_state.title = f"Page: {url.split('/')[-1]}"
        self.current_state.elements = self._generate_mock_elements()
        
        self.action_history.append({
            "action": BrowserAction.NAVIGATE,
            "url": url,
            "timestamp": time.time()
        })
        
        logger.info(f"Mock navigation to {url}")
        return {
            "success": True,
            "url": url,
            "title": self.current_state.title,
            "elements_found": len(self.current_state.elements)
        }
    
    async def click(self, selector: str, element_type: str = "button") -> Dict[str, Any]:
        """Click an element"""
        await self._simulate_delay()
        
        if self._should_fail():
            raise Exception(f"Click failed on {selector}")
            
        # Simulate element interaction
        element = self._find_element(selector)
        if not element:
            raise Exception(f"Element not found: {selector}")
            
        self.action_history.append({
            "action": BrowserAction.CLICK,
            "selector": selector,
            "element_type": element_type,
            "timestamp": time.time()
        })
        
        logger.info(f"Mock click on {selector}")
        return {
            "success": True,
            "element_clicked": selector,
            "element_type": element_type
        }
    
    async def type_text(self, selector: str, text: str) -> Dict[str, Any]:
        """Type text into an element"""
        await self._simulate_delay()
        
        if self._should_fail():
            raise Exception(f"Type failed on {selector}")
            
        element = self._find_element(selector)
        if not element:
            raise Exception(f"Element not found: {selector}")
            
        self.action_history.append({
            "action": BrowserAction.TYPE,
            "selector": selector,
            "text": text,
            "timestamp": time.time()
        })
        
        logger.info(f"Mock type '{text}' into {selector}")
        return {
            "success": True,
            "element": selector,
            "text_entered": text
        }
    
    async def take_screenshot(self, filename: Optional[str] = None) -> Dict[str, Any]:
        """Take a screenshot"""
        await self._simulate_delay()
        
        if self._should_fail():
            raise Exception("Screenshot failed")
            
        self.screenshot_counter += 1
        screenshot_path = filename or f"mock_screenshot_{self.screenshot_counter}.png"
        self.current_state.screenshot_path = screenshot_path
        
        self.action_history.append({
            "action": BrowserAction.SCREENSHOT,
            "filename": screenshot_path,
            "timestamp": time.time()
        })
        
        logger.info(f"Mock screenshot saved: {screenshot_path}")
        return {
            "success": True,
            "screenshot_path": screenshot_path,
            "url": self.current_state.url
        }
    
    async def extract_text(self, selector: Optional[str] = None) -> Dict[str, Any]:
        """Extract text from page or element"""
        await self._simulate_delay()
        
        if self._should_fail():
            raise Exception("Text extraction failed")
            
        if selector:
            element = self._find_element(selector)
            text = element.text if element else "Element not found"
        else:
            text = " ".join([elem.text for elem in self.current_state.elements])
            
        self.action_history.append({
            "action": BrowserAction.EXTRACT_TEXT,
            "selector": selector,
            "timestamp": time.time()
        })
        
        logger.info(f"Mock text extraction: {len(text)} characters")
        return {
            "success": True,
            "text": text,
            "selector": selector
        }
    
    async def extract_elements(self, selector: str) -> Dict[str, Any]:
        """Extract elements matching selector"""
        await self._simulate_delay()
        
        if self._should_fail():
            raise Exception("Element extraction failed")
            
        elements = [elem for elem in self.current_state.elements 
                   if selector.lower() in elem.tag.lower() or selector in elem.xpath]
        
        self.action_history.append({
            "action": BrowserAction.EXTRACT_ELEMENTS,
            "selector": selector,
            "count": len(elements),
            "timestamp": time.time()
        })
        
        logger.info(f"Mock element extraction: {len(elements)} elements found")
        return {
            "success": True,
            "elements": [
                {
                    "tag": elem.tag,
                    "text": elem.text,
                    "xpath": elem.xpath,
                    "visible": elem.visible
                }
                for elem in elements
            ],
            "count": len(elements)
        }
    
    async def wait_for_element(self, selector: str, timeout: int = 10) -> Dict[str, Any]:
        """Wait for element to appear"""
        await self._simulate_delay()
        
        if self._should_fail():
            raise Exception(f"Element {selector} not found within timeout")
            
        element = self._find_element(selector)
        if not element:
            raise Exception(f"Element {selector} not found")
            
        logger.info(f"Mock wait for element: {selector}")
        return {
            "success": True,
            "element_found": selector,
            "timeout": timeout
        }
    
    def get_current_state(self) -> BrowserState:
        """Get current browser state"""
        return self.current_state
    
    def get_action_history(self) -> List[Dict[str, Any]]:
        """Get action history"""
        return self.action_history
    
    def reset(self):
        """Reset browser state"""
        self.current_state = BrowserState(
            url="about:blank",
            title="Blank Page",
            elements=[]
        )
        self.action_history = []
        self.screenshot_counter = 0
    
    def _should_fail(self) -> bool:
        """Determine if action should fail based on error rate"""
        return random.random() < self.error_rate
    
    async def _simulate_delay(self):
        """Simulate realistic delay"""
        delay = random.uniform(*self.delay_range)
        await asyncio.sleep(delay)
    
    def _find_element(self, selector: str) -> Optional[BrowserElement]:
        """Find element by selector"""
        for element in self.current_state.elements:
            if selector in element.xpath or selector in element.text:
                return element
        return None
    
    def _generate_mock_elements(self) -> List[BrowserElement]:
        """Generate mock page elements"""
        elements = [
            BrowserElement(
                tag="button",
                text="Submit",
                attributes={"id": "submit-btn", "class": "btn-primary"},
                xpath="//button[@id='submit-btn']"
            ),
            BrowserElement(
                tag="input",
                text="",
                attributes={"id": "email", "type": "email", "placeholder": "Enter email"},
                xpath="//input[@id='email']"
            ),
            BrowserElement(
                tag="input",
                text="",
                attributes={"id": "password", "type": "password", "placeholder": "Enter password"},
                xpath="//input[@id='password']"
            ),
            BrowserElement(
                tag="div",
                text="Welcome to our website",
                attributes={"class": "welcome-message"},
                xpath="//div[@class='welcome-message']"
            ),
            BrowserElement(
                tag="a",
                text="Login",
                attributes={"href": "/login", "class": "nav-link"},
                xpath="//a[@href='/login']"
            )
        ]
        return elements


class MockOrchestrator:
    """
    Mock Orchestrator for integration testing
    
    Simulates Claude AI decision making and workflow orchestration.
    Provides realistic AI responses and decision patterns.
    """
    
    def __init__(self, success_rate: float = 0.9, response_delay: float = 0.2):
        self.success_rate = success_rate
        self.response_delay = response_delay
        self.decision_history = []
        self.workflow_steps = []
        
    async def analyze_page(self, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze page content and determine next action"""
        await asyncio.sleep(self.response_delay)
        
        if random.random() > self.success_rate:
            raise Exception("AI analysis failed")
            
        # Simulate AI analysis
        analysis = {
            "page_type": self._determine_page_type(page_data),
            "confidence": random.uniform(0.7, 0.95),
            "next_action": self._determine_next_action(page_data),
            "elements_of_interest": self._identify_elements(page_data),
            "risk_assessment": random.choice(["low", "medium", "high"]),
            "recommended_approach": self._get_recommended_approach(page_data)
        }
        
        self.decision_history.append({
            "action": "analyze_page",
            "analysis": analysis,
            "timestamp": time.time()
        })
        
        logger.info(f"Mock AI analysis: {analysis['page_type']} - {analysis['next_action']}")
        return {
            "success": True,
            "analysis": analysis
        }
    
    async def decide_next_action(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Decide next action based on context"""
        await asyncio.sleep(self.response_delay)
        
        if random.random() > self.success_rate:
            raise Exception("AI decision failed")
            
        action = self._generate_action_plan(context)
        
        self.decision_history.append({
            "action": "decide_next_action",
            "context": context,
            "decision": action,
            "timestamp": time.time()
        })
        
        logger.info(f"Mock AI decision: {action['action_type']}")
        return {
            "success": True,
            "action": action
        }
    
    async def validate_action(self, action: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate proposed action"""
        await asyncio.sleep(self.response_delay)
        
        if random.random() > self.success_rate:
            raise Exception("AI validation failed")
            
        validation = {
            "is_safe": random.random() > 0.1,  # 90% safe
            "confidence": random.uniform(0.6, 0.9),
            "risk_factors": self._assess_risks(action, context),
            "recommendations": self._get_recommendations(action, context)
        }
        
        self.decision_history.append({
            "action": "validate_action",
            "action_data": action,
            "validation": validation,
            "timestamp": time.time()
        })
        
        logger.info(f"Mock AI validation: {'SAFE' if validation['is_safe'] else 'RISKY'}")
        return {
            "success": True,
            "validation": validation
        }
    
    async def generate_workflow_plan(self, goal: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate complete workflow plan"""
        await asyncio.sleep(self.response_delay * 2)  # Longer for planning
        
        if random.random() > self.success_rate:
            raise Exception("Workflow planning failed")
            
        plan = self._create_workflow_plan(goal, context)
        
        self.decision_history.append({
            "action": "generate_workflow_plan",
            "goal": goal,
            "plan": plan,
            "timestamp": time.time()
        })
        
        logger.info(f"Mock workflow plan: {len(plan['steps'])} steps")
        return {
            "success": True,
            "plan": plan
        }
    
    def get_decision_history(self) -> List[Dict[str, Any]]:
        """Get AI decision history"""
        return self.decision_history
    
    def reset(self):
        """Reset orchestrator state"""
        self.decision_history = []
        self.workflow_steps = []
    
    def _determine_page_type(self, page_data: Dict[str, Any]) -> str:
        """Determine page type based on content"""
        url = page_data.get("url", "")
        elements = page_data.get("elements", [])
        
        if "login" in url.lower():
            return "login_page"
        elif "signup" in url.lower():
            return "signup_page"
        elif any("form" in elem.get("tag", "") for elem in elements):
            return "form_page"
        elif any("button" in elem.get("tag", "") for elem in elements):
            return "interactive_page"
        else:
            return "content_page"
    
    def _determine_next_action(self, page_data: Dict[str, Any]) -> str:
        """Determine next action based on page analysis"""
        page_type = self._determine_page_type(page_data)
        
        actions = {
            "login_page": "fill_login_form",
            "signup_page": "fill_signup_form",
            "form_page": "complete_form",
            "interactive_page": "click_primary_button",
            "content_page": "extract_information"
        }
        
        return actions.get(page_type, "analyze_content")
    
    def _identify_elements(self, page_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify elements of interest"""
        elements = page_data.get("elements", [])
        return [
            {
                "selector": elem.get("xpath", ""),
                "type": elem.get("tag", ""),
                "priority": random.choice(["high", "medium", "low"]),
                "action": self._suggest_element_action(elem)
            }
            for elem in elements[:3]  # Limit to first 3 elements
        ]
    
    def _get_recommended_approach(self, page_data: Dict[str, Any]) -> str:
        """Get recommended approach for the page"""
        approaches = [
            "proceed_with_caution",
            "standard_automation",
            "manual_review_required",
            "high_confidence_automation"
        ]
        return random.choice(approaches)
    
    def _generate_action_plan(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate action plan"""
        action_types = ["click", "type", "navigate", "extract", "wait"]
        action_type = random.choice(action_types)
        
        return {
            "action_type": action_type,
            "target": f"//{action_type}_element",
            "value": f"test_{action_type}_value" if action_type == "type" else None,
            "confidence": random.uniform(0.7, 0.95),
            "reasoning": f"Mock AI reasoning for {action_type} action"
        }
    
    def _assess_risks(self, action: Dict[str, Any], context: Dict[str, Any]) -> List[str]:
        """Assess risks of proposed action"""
        risks = []
        if action.get("action_type") == "click":
            risks.append("potential_page_navigation")
        if action.get("action_type") == "type":
            risks.append("data_validation_required")
        if random.random() < 0.3:
            risks.append("element_visibility_uncertain")
        return risks
    
    def _get_recommendations(self, action: Dict[str, Any], context: Dict[str, Any]) -> List[str]:
        """Get recommendations for action"""
        recommendations = [
            "verify_element_exists",
            "check_page_loaded",
            "monitor_for_errors"
        ]
        return recommendations[:random.randint(1, 3)]
    
    def _suggest_element_action(self, element: Dict[str, Any]) -> str:
        """Suggest action for element"""
        tag = element.get("tag", "").lower()
        if tag == "button":
            return "click"
        elif tag == "input":
            return "type"
        elif tag == "a":
            return "click"
        else:
            return "extract"
    
    def _create_workflow_plan(self, goal: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create workflow plan"""
        steps = [
            {
                "step": 1,
                "action": "navigate",
                "target": "https://example.com",
                "description": "Navigate to target website"
            },
            {
                "step": 2,
                "action": "analyze",
                "target": "page_content",
                "description": "Analyze page structure and content"
            },
            {
                "step": 3,
                "action": "interact",
                "target": "primary_elements",
                "description": "Interact with key page elements"
            },
            {
                "step": 4,
                "action": "validate",
                "target": "results",
                "description": "Validate action results"
            }
        ]
        
        return {
            "goal": goal,
            "steps": steps,
            "estimated_duration": random.randint(30, 120),
            "confidence": random.uniform(0.8, 0.95),
            "risk_level": random.choice(["low", "medium", "high"])
        }
