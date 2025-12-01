import asyncio
import json
import os
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
import google.generativeai as genai

# ==========================================
# CONFIGURATION
# ==========================================
# 1. PASTE YOUR GEMINI API KEY HERE
GEMINI_API_KEY = ""

# 2. GLOBAL VARIABLES (Will be overwritten by user input)
TARGET_URL = "https://www.wikipedia.org/"
GOAL = "Type 'Artificial Intelligence' into the search bar."

# 3. SETTINGS
MAX_STEPS = 10
HEADLESS = False  # Set to False to watch the browser work

# ==========================================
# 1. HTML CLEANER (Context Optimization)
# ==========================================
class DOMSimplifier:
    """
    Strips raw HTML down to essential interactive elements 
    to fit within Gemini's context window efficiently.
    """
    @staticmethod
    def simplify(html_content: str) -> str:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove heavy/irrelevant tags
        for element in soup(["script", "style", "svg", "path", "head", "meta", "noscript", "footer"]):
            element.decompose()

        # Simplify attributes for remaining tags
        for tag in soup.find_all(True):
            # Keep only crucial attributes for identification
            allowed_attrs = ['id', 'name', 'class', 'href', 'type', 'placeholder', 'aria-label', 'role']
            tag.attrs = {k: v for k, v in tag.attrs.items() if k in allowed_attrs}
            
        return str(soup.prettify())

# ==========================================
# 2. THE BRAIN (GEMINI INTERFACE)
# ==========================================
class AgentPlanner:
    def __init__(self, api_key: str):
        if "YOUR_GEMINI" in api_key:
            raise ValueError("Please replace 'YOUR_GEMINI_API_KEY_HERE' with a real key from aistudio.google.com")
            
        genai.configure(api_key=api_key)
        
        # Initialize Gemini 1.5 Flash
        # We enforce response_mime_type="application/json" for stability
        self.model = genai.GenerativeModel(
            model_name='models/gemini-2.5-flash',
            generation_config={"response_mime_type": "application/json"}
        )

    async def get_next_action(self, current_url: str, dom_snippet: str, history: List[str]) -> Dict:
        print(f"\n[Planner] Thinking about {current_url}...")

        prompt = f"""
        You are a web automation agent.
        
        GOAL: {GOAL}
        PAST ACTIONS: {history}
        CURRENT URL: {current_url}
        
        HTML SNIPPET (Current Page State):
        {dom_snippet[:30000]} 
        
        INSTRUCTIONS:
        Analyze the HTML and determine the next logical step to achieve the goal.
        Return a single JSON object with these keys:
        - "thought": A short explanation of your reasoning.
        - "action": One of ["type", "click", "scrape", "finish"].
        - "selector": The precise CSS selector to interact with.
        - "value": The text to type (if action is 'type') or the instruction for scraping.

        IMPORTANT SELECTOR RULES:
        1. Do NOT use the ':contains()' pseudo-class. It is invalid in standard CSS.
        2. To match text, use XPath (e.g., "//span[contains(text(), 'Boys')]") or simple CSS classes.
        3. If you see search results, prioritize scraping them immediately rather than trying complex filtering.
        """

        try:
            # Call Gemini
            response = await self.model.generate_content_async(prompt)
            
            # The response is guaranteed to be JSON due to generation_config
            plan = json.loads(response.text)
            return plan
            
        except Exception as e:
            print(f"❌ Gemini API Error: {e}")
            return {"action": "finish", "thought": "API call failed."}

# ==========================================
# 3. THE BODY (PLAYWRIGHT AGENT)
# ==========================================
class WebAgent:
    def __init__(self):
        self.planner = AgentPlanner(api_key=GEMINI_API_KEY)
        self.history = []
        self.collected_data = []

    async def run(self):
        async with async_playwright() as p:
            # Launch browser with stealth arguments to avoid detection
            browser = await p.chromium.launch(
                headless=HEADLESS,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox"
                ]
            )
            
            # Create context with a real User Agent to look like a human
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 720},
                device_scale_factor=1,
            )
            
            page = await context.new_page()

            # Extra Stealth: Hide the "webdriver" property that screams "I am a bot"
            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)

            print(f"🚀 Starting Agent.\nTarget: {TARGET_URL}\nGoal: {GOAL}")
            
            try:
                await page.goto(TARGET_URL)
                
                # Main Loop
                for step in range(MAX_STEPS):
                    print(f"\n--- Step {step + 1}/{MAX_STEPS} ---")
                    
                    # 1. Observe
                    try:
                        content = await page.content()
                        clean_dom = DOMSimplifier.simplify(content)
                        current_url = page.url
                    except Exception as e:
                        print(f"Error reading page: {e}")
                        break
                    
                    # 2. Plan
                    plan = await self.planner.get_next_action(current_url, clean_dom, self.history)
                    
                    thought = plan.get('thought')
                    action = plan.get('action')
                    selector = plan.get('selector')
                    value = plan.get('value')
                    
                    print(f"🤖 Thought: {thought}")
                    print(f"👉 Action: {action.upper()} on '{selector}'")

                    # 3. Act
                    try:
                        # Increased timeout to 10 seconds for slower sites like eBay
                        TIMEOUT_MS = 10000 

                        if action == "type":
                            await page.wait_for_selector(selector, state='visible', timeout=TIMEOUT_MS)
                            await page.fill(selector, value)
                            self.history.append(f"Typed '{value}' into {selector}")

                        elif action == "click":
                            await page.wait_for_selector(selector, state='visible', timeout=TIMEOUT_MS)
                            await page.click(selector)
                            self.history.append(f"Clicked {selector}")
                            # Wait for potential navigation
                            try:
                                await page.wait_for_load_state('networkidle', timeout=5000)
                            except:
                                pass

                        elif action == "scrape":
                            print(f"📄 Scraping content from: {selector}")
                            
                            # CRITICAL FIX: Wait for the items to actually exist before scraping
                            # This fixes the "Scraped 0 items" bug on slow sites like eBay
                            try:
                                await page.wait_for_selector(selector, state='attached', timeout=5000)
                            except:
                                print(f"⚠️ Warning: Selector {selector} not found immediately. Attempting scrape anyway.")

                            # Use query_selector_all
                            elements = await page.query_selector_all(selector)
                            
                            data = []
                            for el in elements:
                                text = await el.inner_text()
                                # SMART LINK EXTRACTION (UPDATED): 
                                # 1. Check if element is <a>
                                # 2. Check if element is inside <a>
                                # 3. Check if element contains <a> (descendant)
                                link = await el.evaluate("""el => {
                                    if (el.tagName === 'A') return el.href;
                                    if (el.closest('a')) return el.closest('a').href;
                                    const child = el.querySelector('a');
                                    return child ? child.href : null;
                                }""")
                                
                                if text.strip(): # Only save if there is text
                                    data.append({
                                        "text": text.strip(),
                                        "link": link
                                    })
                            
                            self.collected_data.append({"step": step, "data": data})
                            print(f"✅ Scraped {len(data)} items.")
                            
                            self.history.append(f"Scraped data from {selector}")
                            
                            if value == "finish":
                                print("🏁 Scrape complete. Finishing.")
                                break
                            
                            # If we scraped 0 items, we should tell the AI
                            if len(data) == 0:
                                self.history.append(f"WARNING: Scraped 0 items using {selector}. Try a different selector.")

                        elif action == "finish":
                            print("🏁 Goal achieved.")
                            break
                        
                        else:
                            print(f"⚠️ Unknown action: {action}")

                    except Exception as e:
                        error_msg = f"Failed to execute {action} on {selector}: {str(e)}"
                        print(f"❌ {error_msg}")
                        self.history.append(error_msg)

            finally:
                await browser.close()
                self.save_results()

    def save_results(self):
        if self.collected_data:
            filename = "gemini_agent_results.json"
            with open(filename, "w") as f:
                json.dump(self.collected_data, f, indent=2)
            print(f"\n💾 Data saved to {filename}")
        else:
            print("\n⚠️ No data collected.")

# ==========================================
# EXECUTION (UPDATED)
# ==========================================
if __name__ == "__main__":
    try:
        print("🤖 AI Web Agent Initialized.")
        print("-----------------------------------")
        
        # 1. Ask the user for input dynamically
        target_url = input("🌐 Enter the URL to start at (e.g., https://amazon.com): ").strip()
        user_goal = input("🎯 What should I do? (e.g., Find the price of iPhone 15): ").strip()
        
        if not target_url.startswith("http"):
            target_url = "https://" + target_url
            
        # 2. Update the global variables dynamically
        import sys
        
        TARGET_URL = target_url
        GOAL = user_goal
        
        print(f"\n🚀 Launching Agent for: {target_url}")
        print(f"📋 Mission: {GOAL}\n")

        # 3. Run the agent
        agent = WebAgent()
        asyncio.run(agent.run())

    except ValueError as e:
        print(f"\n❌ SETUP ERROR: {e}")
    except KeyboardInterrupt:
        print("\n🛑 Stopped by user.")
    except Exception as e:
        print(f"\n❌ RUNTIME ERROR: {e}")
