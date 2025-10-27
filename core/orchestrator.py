"""
Claude Orchestrator Module

Analyzes screenshots and decides actions using Claude's Vision API.
The "brain" of the automation system.
"""

import os
import json
import logging
from typing import Optional, Dict, List
from anthropic import Anthropic
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ClaudeOrchestrator:
    """
    Orchestrates browser automation using Claude's Vision API.
    
    Analyzes screenshots to decide what actions to take to achieve goals.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-sonnet-4-20250514"):
        """
        Initialize ClaudeOrchestrator.
        
        Args:
            api_key: Anthropic API key (if None, loads from ANTHROPIC_API_KEY env var)
            model: Claude model to use
        """
        # Load API key from environment if not provided
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not found. "
                "Set it in .env file or pass as parameter."
            )
        
        self.model = model
        self.client = Anthropic(api_key=self.api_key)
        
        logger.info(f"ClaudeOrchestrator initialized with model: {model}")
    
    async def understand_screen_and_decide(
        self,
        screenshot_b64: str,
        goal: str,
        current_step: str,
        page_text: str = "",
        form_fields: str = ""
    ) -> dict:
        """
        Analyze screenshot and decide next action.
        
        Args:
            screenshot_b64: Base64 encoded screenshot
            goal: Overall goal/objective
            current_step: Description of current step
            page_text: Visible text from page (for context)
            form_fields: Form field information (names, types, values)
        
        Returns:
            {
                "action": "click" | "type" | "navigate" | "complete" | "error",
                "target": "selector or text or URL",
                "value": "text to type (if action=type)",
                "reasoning": "why this action",
                "confidence": 0.0 to 1.0,
                "needs_human_review": bool
            }
        """
        logger.info(f"Analyzing screenshot for goal: {goal}")
        logger.info(f"Current step: {current_step}")
        
        # Build prompt for Claude
        prompt = self._build_decision_prompt(goal, current_step, page_text, form_fields)
        
        try:
            # Call Claude API with vision
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": screenshot_b64
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            )
            
            # Parse response
            response_text = response.content[0].text
            logger.info(f"Claude response: {response_text[:200]}...")

            # Strip markdown code blocks if present
            response_text = response_text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:]  # Remove ```json
            elif response_text.startswith('```'):
                response_text = response_text[3:]  # Remove ```
            if response_text.endswith('```'):
                response_text = response_text[:-3]  # Remove trailing ```
            response_text = response_text.strip()

            # Parse JSON
            action_data = json.loads(response_text)
            
            # Validate response
            if not self._validate_action_response(action_data):
                logger.error("Invalid response format from Claude")
                return {
                    "action": "error",
                    "target": "",
                    "value": "",
                    "reasoning": "Invalid response format from Claude",
                    "confidence": 0.0,
                    "needs_human_review": True
                }
            
            logger.info(f"Decision: {action_data['action']} - {action_data['reasoning']}")
            return action_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return {
                "action": "error",
                "target": "",
                "value": "",
                "reasoning": f"Failed to parse Claude response: {str(e)}",
                "confidence": 0.0,
                "needs_human_review": True
            }
        except Exception as e:
            logger.error(f"Error calling Claude API: {e}")
            return {
                "action": "error",
                "target": "",
                "value": "",
                "reasoning": f"API error: {str(e)}",
                "confidence": 0.0,
                "needs_human_review": True
            }
    
    async def generate_workflow_plan(self, natural_language_goal: str) -> List[str]:
        """
        Generate step-by-step workflow plan from natural language goal.

        Args:
            natural_language_goal: User's goal in plain English

        Returns:
            List of step descriptions: ["Step 1", "Step 2", ...]
        """
        logger.info(f"Generating workflow plan for: {natural_language_goal}")

        prompt = f"""Break down this goal into specific, actionable steps for browser automation:

GOAL: {natural_language_goal}

Return ONLY a JSON array of step descriptions. Each step should be:
- Specific and actionable
- In logical order
- Achievable by browser automation
- Clear and concise

Example format:
["Navigate to website.com", "Click login button", "Type email into input field", "Click submit"]

Return only the JSON array, no other text:"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=512,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            response_text = response.content[0].text
            logger.info(f"Workflow plan response: {response_text[:200]}...")

            # Parse JSON array
            steps = json.loads(response_text)

            if not isinstance(steps, list):
                logger.error("Response is not a list")
                return ["Error: Could not generate workflow plan"]

            logger.info(f"Generated {len(steps)} steps")
            return steps

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse workflow plan: {e}")
            return ["Error: Could not parse workflow plan"]
        except Exception as e:
            logger.error(f"Error generating workflow plan: {e}")
            return [f"Error: {str(e)}"]

    async def analyze_and_fill_form(
        self,
        screenshot_b64: str,
        form_fields: str,
        goal: str,
        form_data: Optional[Dict[str, any]] = None
    ) -> Dict[str, any]:
        """
        Analyze form and generate a complete filling plan for all fields at once.

        This is more efficient than the step-by-step approach - analyzes the entire form
        and returns all actions needed to fill it completely.

        Args:
            screenshot_b64: Base64 encoded screenshot
            form_fields: Structured form field information from get_form_fields()
            goal: What the form is for (e.g., "Pizza order form")
            form_data: Optional predefined data to fill (e.g., {"name": "John", "email": "john@example.com"})

        Returns:
            {
                "actions": [
                    {"action": "type", "target": "input[name='custname']", "value": "John Doe"},
                    {"action": "type", "target": "input[name='custemail']", "value": "john@example.com"},
                    {"action": "click", "target": "input[name='size'][value='medium']"},
                    {"action": "click", "target": "input[type='submit']"}
                ],
                "reasoning": "Explanation of the plan",
                "confidence": 0.9,
                "needs_human_review": false
            }
        """
        logger.info(f"Analyzing form for batch filling: {goal}")

        # Build prompt
        prompt = f"""You are a form-filling assistant. Analyze this form screenshot and generate a COMPLETE plan to fill ALL fields at once.

GOAL: {goal}

FORM FIELDS DETECTED:
{form_fields}

PREDEFINED DATA (use this if available):
{json.dumps(form_data, indent=2) if form_data else "None - generate appropriate test data"}

YOUR TASK:
1. Identify ALL form fields visible in the screenshot
2. Generate appropriate data for EACH field (use predefined data if provided, otherwise create realistic test data)
3. Return a COMPLETE list of actions to fill the ENTIRE form and submit it

Return ONLY valid JSON with this structure:
{{
    "actions": [
        {{"action": "type", "target": "input[name='fieldname']", "value": "text to enter"}},
        {{"action": "click", "target": "input[type='radio'][value='option']"}},
        ...
    ],
    "reasoning": "Brief explanation of the filling strategy",
    "confidence": 0.95,
    "needs_human_review": false
}}

ACTION TYPES:
- "type": For text inputs, email, tel, textarea, time, etc. (target = CSS selector, value = text/data)
- "click": For radio buttons, checkboxes, submit buttons (target = CSS selector)
- "select": For dropdown menus (target = CSS selector, value = option to select)

SELECTOR BEST PRACTICES:
- ALWAYS use the exact selectors from FORM FIELDS DETECTED above
- PREFER input[name='exactname'] format (most reliable)
- For radio/checkbox: input[name='fieldname'][value='optionvalue']
- For buttons with text: use "button" selector or click by text (e.g., if FORM FIELDS shows "button (text: 'Submit order')", use "button" as target)
- For submit buttons: use "button" or "input[type='submit']" depending on what's detected

IMPORTANT RULES:
1. Include actions for ALL visible form fields, not just some
2. Use realistic, appropriate test data for each field type
3. Follow logical order: text fields first, then radio/checkboxes, then submit
4. For time fields, use format "HH:MM" (e.g., "19:00")
5. For email fields, use valid email format
6. For phone fields, use valid phone format
7. Set needs_human_review=true only for sensitive actions (payment, delete account, etc.)
8. The submit button is usually at the end - make sure to include it!

Return ONLY the JSON, no other text:"""

        try:
            # Call Claude API with vision
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,  # Larger token limit for comprehensive form analysis
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": screenshot_b64
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            )

            # Parse response
            response_text = response.content[0].text
            logger.info(f"Form analysis response: {response_text[:300]}...")

            # Strip markdown code blocks if present
            response_text = response_text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:]  # Remove ```json
            elif response_text.startswith('```'):
                response_text = response_text[3:]  # Remove ```
            if response_text.endswith('```'):
                response_text = response_text[:-3]  # Remove trailing ```
            response_text = response_text.strip()

            # Parse JSON
            plan = json.loads(response_text)

            # Validate response
            if "actions" not in plan or not isinstance(plan["actions"], list):
                logger.error("Invalid form filling plan - missing actions array")
                return {
                    "actions": [],
                    "reasoning": "Failed to generate valid form filling plan",
                    "confidence": 0.0,
                    "needs_human_review": True
                }

            logger.info(f"Generated plan with {len(plan['actions'])} actions")
            return plan

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse form analysis response: {e}")
            return {
                "actions": [],
                "reasoning": f"JSON parse error: {str(e)}",
                "confidence": 0.0,
                "needs_human_review": True
            }
        except Exception as e:
            logger.error(f"Error analyzing form: {e}")
            return {
                "actions": [],
                "reasoning": f"API error: {str(e)}",
                "confidence": 0.0,
                "needs_human_review": True
            }
    
    def _build_decision_prompt(self, goal: str, current_step: str, page_text: str, form_fields: str = "") -> str:
        """
        Build comprehensive prompt for Claude to analyze screenshot.
        
        Args:
            goal: Overall goal
            current_step: Current step description
            page_text: Page text for context
            form_fields: Form field information
        
        Returns:
            Formatted prompt string
        """
        prompt = f"""You are a browser automation assistant. Analyze this screenshot and decide the next action.

GOAL: {goal}
CURRENT STEP: {current_step}

PAGE TEXT (for context):
{page_text[:500] if page_text else "No text available"}...

FORM FIELDS ON PAGE (use these EXACT selectors):
{form_fields if form_fields else "No form fields detected"}


Analyze the screenshot and return ONLY valid JSON with this exact structure:
{{
    "action": "click" | "type" | "navigate" | "complete" | "error",
    "target": "CSS selector or text or URL",
    "value": "text to type (only if action=type, otherwise empty string)",
    "reasoning": "brief explanation of why this action",
    "confidence": 0.85,
    "needs_human_review": false
}}

ACTION TYPES:
- "click": Click an element (target = CSS selector like "button#submit" or "text=Click Here")
- "type": Type text into input (target = CSS selector like "input[name='email']" or "#custname", value = text to type)
- "navigate": Go to URL (target = full URL)
- "complete": Goal is achieved (target = "", value = "")
- "error": Cannot proceed (target = "", value = "", explain in reasoning)

SELECTOR BEST PRACTICES:
- PREFER name attribute: input[name='custname'] over input[type='text']:first-of-type
- PREFER id attribute: #email over input[type='email']
- AVOID pseudo-classes like :first-of-type, :nth-child - they may not work reliably
- Use specific attributes when available (name, id, placeholder, aria-label)
- READ field names CAREFULLY from the screenshot - don't guess or make up names
- If you can't see the exact name attribute, use a more general selector like input[type='tel']

IMPORTANT RULES:
1. For input fields (text boxes, search boxes, etc.), use "type" action directly - clicking first is optional
2. When you see an empty form field that needs data, use "type" action immediately with the appropriate value
3. After typing into a search box, the system will automatically press Enter - don't try to click suggestions!
4. If you see search results on the page, look for result links and click them using "text=..." format
5. Use CSS selectors for "target" when possible (e.g., "input[name='q']", "button#submit")
6. Use "text=..." for clicking by text (e.g., "text=Search", "text=Submit")
7. Set confidence lower if uncertain (0.0 to 1.0)
8. Set needs_human_review=true for risky actions (delete, submit payment, etc.)
9. Use action="complete" when goal is fully achieved (e.g., you've clicked a search result and read the page)
10. Use action="error" if goal cannot be completed
11. PREFER "type" over "click" for form fields - the browser controller will handle focusing automatically
12. For forms: identify the field selector and use "type" with appropriate data, don't click first
13. NEVER fill the same field twice - if a field already has data, move to the next empty field
14. Look at the CURRENT STEP number - if you're on step 3+, the first fields are likely already filled

Return ONLY the JSON, no other text:"""
        
        return prompt
    
    def _validate_action_response(self, response: dict) -> bool:
        """
        Validate action response has required fields.
        
        Args:
            response: Action dictionary from Claude
        
        Returns:
            True if valid, False otherwise
        """
        required_fields = ["action", "target", "reasoning", "confidence"]
        
        # Check required fields exist
        if not all(field in response for field in required_fields):
            logger.error(f"Missing required fields. Got: {response.keys()}")
            return False
        
        # Validate action type
        valid_actions = ["click", "type", "navigate", "complete", "error"]
        if response["action"] not in valid_actions:
            logger.error(f"Invalid action: {response['action']}")
            return False
        
        # Validate confidence
        try:
            confidence = float(response["confidence"])
            if not (0.0 <= confidence <= 1.0):
                logger.error(f"Confidence out of range: {confidence}")
                return False
        except (ValueError, TypeError):
            logger.error(f"Invalid confidence value: {response['confidence']}")
            return False
        
        return True


# Example usage
async def main():
    """Example usage of ClaudeOrchestrator."""
    import asyncio
    import sys
    sys.path.append('..')
    from browser_controller import BrowserController
    
    # Initialize
    orchestrator = ClaudeOrchestrator()
    
    async with BrowserController(headless=False) as browser:
        # Navigate to a page
        await browser.navigate("https://example.com")
        
        # Capture screenshot
        _, _, screenshot_b64 = await browser.capture_screenshot()
        page_text = await browser.get_page_text()
        
        # Ask Claude what to do
        decision = await orchestrator.understand_screen_and_decide(
            screenshot_b64=screenshot_b64,
            goal="Read the content on this page",
            current_step="Just landed on example.com",
            page_text=page_text
        )
        
        print("\n=== Claude's Decision ===")
        print(f"Action: {decision['action']}")
        print(f"Target: {decision['target']}")
        print(f"Reasoning: {decision['reasoning']}")
        print(f"Confidence: {decision['confidence']}")
        
    # Test workflow planning
    print("\n=== Workflow Planning Test ===")
    plan = await orchestrator.generate_workflow_plan(
        "Search for Anthropic on DuckDuckGo"
    )
    print("Generated plan:")
    for i, step in enumerate(plan, 1):
        print(f"{i}. {step}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
