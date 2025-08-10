import os
import time
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import logging
import pyttsx3
import re
import requests
from together import Together
import difflib
from difflib import get_close_matches
import speech_recognition as sr
import uuid
import tkinter as tk
import threading
from tkinter import PhotoImage
import base64
from io import BytesIO
from PIL import Image, ImageTk

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logger.info("Starting script...")

load_dotenv("environment.env")

api_key = os.getenv("TOGETHER_API_KEY")
logger.info(f"Together API key found: {'Yes' if api_key else 'No'}")
if not api_key:
    raise Exception("❌ TOGETHER_API_KEY not found in environment.env file!")

# Initialize Together client
client = Together(api_key=api_key)
MODEL = "mistralai/Mixtral-8x7B-Instruct-v0.1"

# Initialize speech recognition (from a.py logic)
recognizer = sr.Recognizer()
microphone = sr.Microphone()

# Track last action and last search results for context
last_action = None
last_search_results = []

# Microphone icon as base64 PNG (simple black mic, 32x32)
MIC_ICON_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAABFUlEQVR4Ae3XwQnCMBiG4e8QwQnC"
    "wQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnC"
    "wQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnC"
    "wQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnC"
    "wQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnC"
    "wQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnC"
    "wQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnC"
    "wQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnC"
    "wQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnC"
    "wQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnC"
    "wQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnC"
    "wQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnC"
    "wQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnC"
    "wQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnC"
    "wQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnC"
    "wQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnC"
    "wQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnC"
    "wQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnC"
    "wQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnC"
    "wQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnC"
    "wQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnC"
    "wQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnC"
    "wQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnC"
    "wQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnC"
    "wQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnC"
    "wQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnC"
    "wQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnC"
    "wQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnC"
    "wQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnC"
    "wQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnCwQnC"
)

class AnimatedOverlay:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Bot Status")
        self.root.geometry("120x120+20+20")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.canvas = tk.Canvas(self.root, width=120, height=120, bg="black", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.status = "Ready"
        self.pulse_radius = 40
        self.pulse_growing = True
        self._pending_status = None
        self.root.after(30, self.animate)

    def set_status(self, status):
        self._pending_status = status

    def animate(self):
        self.canvas.delete("all")
        # Animate pulsing circle
        color = "#1abc9c" if self.status == "Listening..." else "#f39c12" if self.status == "Processing..." else "#333"
        if self.status in ["Listening...", "Processing..."]:
            self.canvas.create_oval(
                60 - self.pulse_radius, 60 - self.pulse_radius,
                60 + self.pulse_radius, 60 + self.pulse_radius,
                fill=color, outline="", stipple="gray50"
            )
            # Animate radius
            if self.pulse_growing:
                self.pulse_radius += 1
                if self.pulse_radius >= 50:
                    self.pulse_growing = False
            else:
                self.pulse_radius -= 1
                if self.pulse_radius <= 40:
                    self.pulse_growing = True
        # Improved mic icon
        # Mic head (main oval)
        self.canvas.create_oval(48, 38, 72, 78, fill="white", outline="#888", width=2)
        # Mic body (vertical line)
        self.canvas.create_line(60, 78, 60, 95, fill="white", width=5, capstyle=tk.ROUND)
        # Mic base (thick arc)
        self.canvas.create_arc(50, 90, 70, 110, start=0, extent=180, style=tk.ARC, outline="white", width=4)
        # Mic head shine (smaller oval)
        self.canvas.create_oval(54, 44, 66, 60, fill="#e0e0e0", outline="", width=0)
        # Mic grill lines
        self.canvas.create_line(54, 55, 66, 55, fill="#bbb", width=2)
        self.canvas.create_line(54, 62, 66, 62, fill="#bbb", width=2)
        # Draw status text
        self.canvas.create_text(60, 110, text=self.status, fill="white", font=("Arial", 12, "bold"))
        # Update status if needed
        if self._pending_status is not None:
            self.status = self._pending_status
            self._pending_status = None
        self.root.after(30, self.animate)

    def run(self):
        self.root.mainloop()

def speak(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()

def setup_playwright():
    p = sync_playwright().start()
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    return p, browser, page

def find_element_smart(page, possible_selectors, field_name=None):
    # Try Playwright's robust selectors first if field_name is provided
    if field_name:
        # Try by label
        try:
            el = page.get_by_label(field_name)
            if el and el.is_visible():
                return el
        except Exception:
            pass
        # Try by test id
        try:
            el = page.get_by_test_id(field_name)
            if el and el.is_visible():
                return el
        except Exception:
            pass
        # Try by role (for buttons, inputs, etc.)
        try:
            el = page.get_by_role("textbox", name=field_name)
            if el and el.is_visible():
                return el
        except Exception:
            pass
    # Fallback to provided selectors
    for selector in possible_selectors:
        try:
            el = page.query_selector(selector)
            if el and el.is_visible():
                return el
        except Exception:
            continue
    return None

def universal_login(page, username, password):
    username_selectors = [
        'input[type="email"]', 'input[name*="email"]', 'input[id*="email"]',
        'input[type="text"]', 'input[name*="user"]', 'input[id*="user"]'
    ]
    password_selectors = [
        'input[type="password"]', 'input[name*="pass"]', 'input[id*="pass"]'
    ]
    submit_selectors = [
        'button[type="submit"]', 'input[type="submit"]', 'button', 'input[type="button"]'
    ]
    # Try robust selectors first
    user_field = find_element_smart(page, username_selectors, field_name="Username")
    if not user_field:
        user_field = find_element_smart(page, username_selectors, field_name="Email")
    pass_field = find_element_smart(page, password_selectors, field_name="Password")
    submit_btn = None
    # Try by role for submit button
    try:
        submit_btn = page.get_by_role("button", name="Login")
        if not submit_btn or not submit_btn.is_visible():
            submit_btn = None
    except Exception:
        pass
    if not submit_btn:
        submit_btn = find_element_smart(page, submit_selectors, field_name="Login")
    if user_field and pass_field:
        user_field.fill("")
        user_field.type(username)
        pass_field.fill("")
        pass_field.type(password)
        if submit_btn:
            submit_btn.click()
            print("Login attempted.")
            speak("Login attempted.")
        return True
    print("Could not find login fields/buttons automatically.")
    speak("Could not find login fields or buttons automatically.")
    return False

def universal_search(page, search_term):
    search_bar_selectors = [
        'input[type="search"]', 'input[name*="search"]', 'input[id*="search"]',
        'input[placeholder*="Search"]', 'input[aria-label*="Search"]',
        'input[type="text"]'
    ]
    # Try robust selectors first
    search_box = None
    try:
        search_box = page.get_by_role("searchbox")
        if not search_box or not search_box.is_visible():
            search_box = None
    except Exception:
        pass
    if not search_box:
        search_box = find_element_smart(page, search_bar_selectors, field_name="Search")
    if not search_box:
        print("No search bar found.")
        speak("No search bar found.")
        return False
    search_box.fill("")
    search_box.type(search_term)
    search_box.press('Enter')
    print("Search submitted with Enter key.")
    speak("Search submitted.")
    return True

def extract_selector(ai_response):
    # Try to extract from a CSS code block
    code_block = re.search(r"```css\s*([\s\S]*?)```", ai_response, re.IGNORECASE)
    if code_block:
        selector = code_block.group(1).strip()
        for line in selector.splitlines():
            line = line.strip()
            if line:
                # Clean up: only take up to first {, space, or newline
                line = re.split(r'[\s{]', line)[0]
                return line
    code_block = re.search(r"```\s*([\s\S]*?)```", ai_response)
    if code_block:
        selector = code_block.group(1).strip()
        for line in selector.splitlines():
            line = line.strip()
            if line:
                line = re.split(r'[\s{]', line)[0]
                return line
    inline = re.search(r"`([^`]+)`", ai_response)
    if inline:
        line = inline.group(1).strip()
        line = re.split(r'[\s{]', line)[0]
        return line
    lines = ai_response.splitlines()
    for line in lines:
        line = line.strip()
        if line and not line.lower().startswith("explanation") and not line.startswith("*") and not line.lower().startswith("to "):
            line = re.split(r'[\s{]', line)[0]
            return line
    return ai_response.strip()

def extract_ordinal(text):
    words = {
        "first": 0, "second": 1, "third": 2, "fourth": 3, "fifth": 4,
        "sixth": 5, "seventh": 6, "eighth": 7, "ninth": 8, "tenth": 9
    }
    for word, idx in words.items():
        if word in text:
            return idx
    match = re.search(r'(\d+)(st|nd|rd|th)?', text)
    if match:
        return int(match.group(1)) - 1
    return None

def fuzzy_match_title(user_input, item_info):
    texts = [text for _, text, _ in item_info]
    matches = get_close_matches(user_input, texts, n=1, cutoff=0.4)
    if matches:
        for i, text, elem in item_info:
            if text == matches[0]:
                return i, elem
    return None, None

def save_debug_info(page, context):
    """Save a screenshot and HTML dump for debugging when selectors fail."""
    try:
        fname = f"debug_{context}_{uuid.uuid4().hex[:8]}"
        page.screenshot(path=f"{fname}.png")
        with open(f"{fname}.html", "w", encoding="utf-8") as f:
            f.write(page.content())
        print(f"[DEBUG] Saved screenshot and HTML as {fname}.png/.html")
    except Exception as e:
        print(f"[DEBUG] Failed to save debug info: {e}")

def handle_command(page, command):
    tokens = command.lower().split()
    if not tokens:
        return

    if tokens[0] == "open" and len(tokens) > 1:
        url = tokens[1]
        if not url.startswith("http"):
            if '.' not in url:
                url += ".com"
                url = "https://" + url
            else:
                url = "https://" + url
        try:
            page.goto(url)
            print(f"Opened {url}")
            speak(f"Opened {url}")
        except Exception as e:
            print(f"[ERROR] Failed to open {url}: {e}")
            speak(f"Failed to open {url}.")
            save_debug_info(page, "open_url")
        return

    if tokens[0] == "search":
        search_term = " ".join(tokens[1:])
        try:
            search_box = page.get_by_role("searchbox")
            if not search_box or not search_box.is_visible():
                search_box = None
        except Exception:
            search_box = None
        if not search_box:
            search_bar_selectors = [
                'input[type="search"]', 'input[name*="search"]', 'input[id*="search"]',
                'input[placeholder*="Search"]', 'input[aria-label*="Search"]',
                'input[type="text"]'
            ]
            search_box = find_element_smart(page, search_bar_selectors, field_name="Search")
        if search_box:
            try:
                search_box.fill("")
                search_box.type(search_term)
                search_box.press('Enter')
                print(f"Search submitted.")
                speak("Search submitted.")
            except Exception as e:
                print(f"[ERROR] Failed to type/search: {e}")
                speak("Failed to submit search.")
                save_debug_info(page, "search")
            return
        print("No search bar found after waiting.")
        speak("No search bar found.")
        save_debug_info(page, "search_not_found")
        return

    if tokens[0] == "login":
        username = input("Enter username: ")
        password = input("Enter password: ")
        user_field = find_element_smart(page, [
            'input[type="email"]', 'input[name*="email"]', 'input[id*="email"]',
            'input[type="text"]', 'input[name*="user"]', 'input[id*="user"]'
        ], field_name="Username")
        if not user_field:
            user_field = find_element_smart(page, [
                'input[type="email"]', 'input[name*="email"]', 'input[id*="email"]',
                'input[type="text"]', 'input[name*="user"]', 'input[id*="user"]'
            ], field_name="Email")
        pass_field = find_element_smart(page, [
            'input[type="password"]', 'input[name*="pass"]', 'input[id*="pass"]'
        ], field_name="Password")
        submit_btn = None
        try:
            submit_btn = page.get_by_role("button", name="Login")
            if not submit_btn or not submit_btn.is_visible():
                submit_btn = None
        except Exception:
            pass
        if not submit_btn:
            submit_btn = find_element_smart(page, [
                'button[type="submit"]', 'input[type="submit"]', 'button', 'input[type="button"]'
            ], field_name="Login")
        if user_field and pass_field:
            try:
                user_field.fill("")
                user_field.type(username)
                pass_field.fill("")
                pass_field.type(password)
                if submit_btn:
                    submit_btn.click()
                    print("Login attempted.")
                    speak("Login attempted.")
            except Exception as e:
                print(f"[ERROR] Failed to fill login fields: {e}")
                speak("Login failed.")
                save_debug_info(page, "login")
            return
        print("Could not find login fields/buttons automatically.")
        speak("Could not find login fields or buttons automatically.")
        save_debug_info(page, "login_not_found")
        return

    # Type in field: "type <text> in <field>"
    match = re.match(r"type (.+) in (.+)", command, re.IGNORECASE)
    if match:
        text, field = match.group(1), match.group(2)
        if not field.strip():
            print("No field specified. Please say the field name or try again.")
            speak("No field specified. Please say the field name or try again.")
            return
        # Direct selector: 'type ... in selector ...'
        sel_match = re.match(r"selector (.+)", field, re.IGNORECASE)
        if sel_match:
            selector = sel_match.group(1).strip()
            try:
                field_elem = page.wait_for_selector(selector, timeout=5000)
                field_elem.fill("")
                field_elem.type(text)
                print(f"Typed '{text}' in selector '{selector}'.")
                speak(f"Typed {text} in the selected field.")
                return
            except PlaywrightTimeoutError:
                print("Element not found or not interactable after waiting.")
                speak("Element not found or not interactable after waiting.")
                return
        # Try robust selectors first
        try:
            field_elem = page.get_by_label(field)
            if field_elem and field_elem.is_visible():
                field_elem.fill("")
                field_elem.type(text)
                print(f"Typed '{text}' in field '{field}' by label.")
                speak(f"Typed {text} in {field}.")
                return
        except Exception:
            pass
        try:
            field_elem = page.get_by_test_id(field)
            if field_elem and field_elem.is_visible():
                field_elem.fill("")
                field_elem.type(text)
                print(f"Typed '{text}' in field '{field}' by test id.")
                speak(f"Typed {text} in {field}.")
                return
        except Exception:
            pass
        try:
            field_elem = page.get_by_role("textbox", name=field)
            if field_elem and field_elem.is_visible():
                field_elem.fill("")
                field_elem.type(text)
                print(f"Typed '{text}' in field '{field}' by role.")
                speak(f"Typed {text} in {field}.")
                return
        except Exception:
            pass
        # AI + heuristics fallback
        print(f"Trying to type '{text}' in '{field}' (AI + heuristics fallback)...")
        speak(f"Trying to type {text} in {field} using AI and heuristics.")
        html = page.content()
        prompt = (
            f"Given the following HTML, what is the best Playwright-compatible CSS selector to find the field for '{field}'? "
            f"Respond with only the selector string, no explanation, no code block, no curly braces.\nHTML:\n" + html[:3000]
        )
        selector = None
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=100,
            )
            print(f"AI raw response: {response}")
            ai_content = response.choices[0].message.content.strip()
            selector = extract_selector(ai_content)
            print(f"AI suggested selector: {selector}")
            try:
                field_elem = page.wait_for_selector(selector, timeout=5000)
                field_elem.fill("")
                field_elem.type(text)
                print(f"Typed '{text}' in '{field}'.")
                speak(f"Typed {text} in {field}.")
                return
            except PlaywrightTimeoutError:
                print("AI selector did not work, trying heuristics...")
        except Exception as e:
            print(f"AI error: {e}")
            print("Trying heuristics...")
        # Heuristic fallback for common fields
        field_lower = field.lower()
        heuristics = []
        if any(k in field_lower for k in ["email"]):
            heuristics = [
                'input[type="email"]', 'input[name*="email"]', 'input[id*="email"]',
                'input[placeholder*="email"]', 'input[aria-label*="email"]'
            ]
        elif any(k in field_lower for k in ["user", "username", "login"]):
            heuristics = [
                'input[name*="user"]', 'input[id*="user"]', 'input[placeholder*="user"]',
                'input[aria-label*="user"]', 'input[type="text"]'
            ]
        elif any(k in field_lower for k in ["pass", "password"]):
            heuristics = [
                'input[type="password"]', 'input[name*="pass"]', 'input[id*="pass"]',
                'input[placeholder*="pass"]', 'input[aria-label*="pass"]'
            ]
        elif any(k in field_lower for k in ["search"]):
            heuristics = [
                'input[type="search"]', 'input[name*="search"]', 'input[id*="search"]',
                'input[placeholder*="search"]', 'input[aria-label*="search"]', 'input[type="text"]'
            ]
        else:
            heuristics = [
                f'input[name*="{field_lower}"]', f'input[id*="{field_lower}"]',
                f'input[placeholder*="{field_lower}"]', f'input[aria-label*="{field_lower}"]',
                'input[type="text"]', 'textarea'
            ]
        for sel in heuristics:
            try:
                field_elem = page.wait_for_selector(sel, timeout=2000)
                if field_elem and field_elem.is_visible():
                    field_elem.fill("")
                    field_elem.type(text)
                    print(f"Typed '{text}' in '{field}' using heuristic selector '{sel}'.")
                    speak(f"Typed {text} in {field}.")
                    return
            except PlaywrightTimeoutError:
                continue
        # If all else fails, list visible input fields for user to pick
        print("Could not find the field automatically. Listing visible input fields:")
        speak("I could not find the field. Here are some visible fields. Say 'type ... in field number 1' to select.")
        input_elems = page.query_selector_all('input, textarea')
        visible_fields = []
        for i, elem in enumerate(input_elems):
            try:
                if elem.is_visible():
                    label = elem.get_attribute('aria-label') or elem.get_attribute('placeholder') or elem.get_attribute('name') or elem.get_attribute('id') or f"input #{i}"
                    visible_fields.append((i, label, elem))
            except Exception:
                continue
        for i, label, _ in visible_fields:
            print(f"Field #{i}: {label}")
            speak(f"Field number {i}: {label}")
        page._input_field_suggestions = [elem for _, _, elem in visible_fields]
        return

    # Type in focused field: "type <text>"
    match = re.match(r"type (.+)", command, re.IGNORECASE)
    if match:
        text = match.group(1)
        # Try to type in the currently focused field
        try:
            focused = page.evaluate_handle("() => document.activeElement")
            tag = focused.get_property("tagName").json_value().lower()
            if tag in ["input", "textarea"]:
                focused.fill("")
                focused.type(text)
                print(f"Typed '{text}' in the focused field.")
                speak(f"Typed {text} in the focused field.")
                return
            else:
                print("Focused element is not a text field.")
                speak("Focused element is not a text field.")
        except Exception as e:
            print(f"Error typing in focused field: {e}")
            speak("Could not type in the focused field.")
        return

    # Click element: "click <something>" or "click selector <css_selector>"
    match_selector = re.match(r"click selector (.+)", command, re.IGNORECASE)
    if match_selector:
        selector = match_selector.group(1).strip()
        print(f"Trying to click element by selector: {selector}")
        speak(f"Trying to click element by selector.")
        try:
            elem = page.wait_for_selector(selector, timeout=5000)
            if elem and elem.is_visible():
                try:
                    elem.scroll_into_view_if_needed()
                except Exception:
                    pass
                elem.click()
                print(f"Clicked element with selector: {selector}")
                speak(f"Clicked element with selector.")
                return
            else:
                print("Element found but not visible.")
        except PlaywrightTimeoutError:
            print("Element not found or not clickable after waiting in main page. Trying iframes...")
            # Try all iframes
            frames = page.frames
            for frame in frames:
                try:
                    elem = frame.wait_for_selector(selector, timeout=2000)
                    if elem and elem.is_visible():
                        try:
                            elem.scroll_into_view_if_needed()
                        except Exception:
                            pass
                        elem.click()
                        print(f"Clicked element with selector: {selector} in iframe.")
                        speak(f"Clicked element with selector in iframe.")
                        return
                except Exception:
                    continue
            print("Element not found or not clickable after waiting in any frame.")
            speak("Element not found or not clickable after waiting.")
            suggest_clickable_elements(page)
        return

    # Click by suggestion number: click #<number>
    match_number = re.match(r"click #(\d+)", command, re.IGNORECASE)
    if match_number:
        idx = int(match_number.group(1))
        if hasattr(page, "_clickable_suggestions") and 0 <= idx < len(page._clickable_suggestions):
            elem = page._clickable_suggestions[idx]
            try:
                elem.scroll_into_view_if_needed()
            except Exception:
                pass
            elem.click()
            print(f"Clicked suggested element #{idx}.")
            speak(f"Clicked suggested element number {idx}.")
            return
        else:
            print("No such suggestion.")
            speak("No such suggestion.")
        return

    # Click by visible text: click <something>
    match_click = re.match(r"click (.+)", command, re.IGNORECASE)
    if match_click:
        target = match_click.group(1).strip()
        # Try robust Playwright selectors first
        try:
            elem = page.get_by_role("button", name=target)
            if elem and elem.is_visible():
                try:
                    elem.scroll_into_view_if_needed()
                except Exception:
                    pass
                elem.click()
                print(f"Clicked '{target}' using role selector.")
                speak(f"Clicked {target}.")
                return
        except Exception:
            pass
        try:
            elem = page.get_by_label(target)
            if elem and elem.is_visible():
                try:
                    elem.scroll_into_view_if_needed()
                except Exception:
                    pass
                elem.click()
                print(f"Clicked '{target}' using label selector.")
                speak(f"Clicked {target}.")
                return
        except Exception:
            pass
        try:
            elem = page.get_by_test_id(target)
            if elem and elem.is_visible():
                try:
                    elem.scroll_into_view_if_needed()
                except Exception:
                    pass
                elem.click()
                print(f"Clicked '{target}' using test id selector.")
                speak(f"Clicked {target}.")
                return
        except Exception:
            pass
        # Try Playwright's text selector directly
        try:
            elem = page.locator(f'text="{target}"').first
            if elem and elem.is_visible():
                try:
                    elem.scroll_into_view_if_needed()
                except Exception:
                    pass
                elem.click()
                print(f"Clicked '{target}' using text selector.")
                speak(f"Clicked {target}.")
                return
            else:
                print("Element found but not visible.")
        except Exception:
            print("Text selector did not work, trying AI fallback...")
        html = page.content()
        prompt = (
            f"Given the following HTML, what is the best Playwright-compatible CSS selector or text selector to find and click a clickable element (like a link or button) whose visible text contains or is similar to '{target}'? "
            f"Do NOT use :contains(). If the element is best found by visible text, respond with Playwright's text selector syntax, e.g., text=\"{target}\". "
            f"Respond with only the selector string.\nHTML:\n" + html[:3000]
        )
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=100,
            )
            print(f"AI raw response: {response}")  # Debug: show full response
            ai_content = response.choices[0].message.content.strip()
            selector = extract_selector(ai_content)
            print(f"AI suggested selector: {selector}")
            # If selector looks like a text selector, use Playwright's text selector API
            selector = selector.strip().strip("'").strip('"')
            if selector.startswith('text=') or selector.startswith('text:"') or selector.startswith('text\"') or selector.startswith('text\'='):
                try:
                    elem = page.locator(selector).first
                    if elem and elem.is_visible():
                        try:
                            elem.scroll_into_view_if_needed()
                        except Exception:
                            pass
                        elem.click()
                        print(f"Clicked '{target}' using AI text selector.")
                        speak(f"Clicked {target}.")
                        return
                except Exception as e:
                    print(f"AI text selector error: {e}")
            else:
                # Try as CSS selector
                try:
                    elem = page.wait_for_selector(selector, timeout=5000)
                    if elem and elem.is_visible():
                        try:
                            elem.scroll_into_view_if_needed()
                        except Exception:
                            pass
                        elem.click()
                        print(f"Clicked '{target}' using AI CSS selector.")
                        speak(f"Clicked {target}.")
                        return
                except Exception as e:
                    print(f"AI CSS selector error: {e}")
            print("AI selector did not work, trying heuristics...")
        except Exception as e:
            print(f"AI error: {e}")
            print("Trying heuristics...")
        # Heuristic fallback for clickable elements
        selectors = [
            'a', 'button', '[role=button]', '[role=link]', '[tabindex="0"]', '[onclick]', '[data-testid]', '[aria-label]'
        ]
        clickable = []
        for sel in selectors:
            for elem in page.query_selector_all(sel):
                if elem.is_visible():
                    text = None
                    try:
                        text = elem.inner_text().strip()
                    except Exception:
                        pass
                    if not text:
                        try:
                            text = elem.get_attribute('aria-label') or elem.get_attribute('title') or elem.get_attribute('name') or elem.get_attribute('id')
                        except Exception:
                            text = None
                    if text:
                        clickable.append((text, elem))
        # Remove duplicates by text
        seen = set()
        unique_clickable = []
        for text, elem in clickable:
            if text not in seen:
                unique_clickable.append((text, elem))
                seen.add(text)
        clickable = [(i, text, elem) for i, (text, elem) in enumerate(unique_clickable)]
        # Try ordinal
        idx = extract_ordinal(target)
        if idx is not None and idx < len(clickable):
            clickable[idx][2].click()
            print(f"Clicked item: {clickable[idx][1]}")
            speak(f"Clicked item {clickable[idx][1]}")
            return
        # Try fuzzy match
        idx, elem = fuzzy_match_title(target, clickable)
        if elem:
            elem.click()
            print(f"Clicked item: {clickable[idx][1]}")
            speak(f"Clicked item {clickable[idx][1]}")
            return
        print("Could not find clickable element by heuristics.")
        speak("Could not find clickable element by heuristics.")
        suggest_clickable_elements(page)
        return

    # Play command: "play <something>"
    match = re.match(r"play (.+)", command, re.IGNORECASE)
    if match:
        target = match.group(1)
        print(f"Trying to play '{target}' (AI fallback)...")
        speak(f"Trying to play {target} using AI.")
        html = page.content()
        prompt = (
            f"Given the following HTML, what is the best CSS selector to find and click the element to play '{target}'? "
            f"If on YouTube, this should be the first video or the video matching '{target}'. "
            f"Respond with only the selector string.\nHTML:\n" + html[:3000]
        )
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=100,
            )
            print(f"AI raw response: {response}")  # Debug: show full response
            ai_content = response.choices[0].message.content.strip()
            selector = extract_selector(ai_content)
            print(f"AI suggested selector: {selector}")
            try:
                elem = page.wait_for_selector(selector, timeout=5000)
                elem.click()
                print(f"Played '{target}'.")
                speak(f"Played {target}.")
                return
            except PlaywrightTimeoutError:
                print("Element not found or not clickable after waiting.")
                speak("Element not found or not clickable after waiting.")
        except Exception as e:
            print(f"AI error: {e}")
            speak("AI could not help with playing.")
        return

    # Scroll up/down commands
    if command.strip().lower() == "scroll up":
        try:
            page.evaluate("() => window.scrollBy(0, -500)")
            print("Scrolled up.")
            speak("Scrolled up.")
        except Exception as e:
            print(f"Scroll up error: {e}")
            speak("Could not scroll up.")
        return
    if command.strip().lower() == "scroll down":
        try:
            page.evaluate("() => window.scrollBy(0, 500)")
            print("Scrolled down.")
            speak("Scrolled down.")
        except Exception as e:
            print(f"Scroll down error: {e}")
            speak("Could not scroll down.")
        return

    # Universal click item by ordinal or fuzzy title: 'click item <target>'
    match_item = re.match(r"click item (.+)", command, re.IGNORECASE)
    if match_item:
        user_input = match_item.group(1).strip()
        # Try to find clickable items: links, buttons, cards, etc.
        selectors = [
            'a', 'button', '[role=button]', '[role=link]', '[tabindex="0"]', '[onclick]', '[data-testid]', '[aria-label]'
        ]
        clickable = []
        for sel in selectors:
            for elem in page.query_selector_all(sel):
                if elem.is_visible():
                    # Try to get the most descriptive text
                    text = elem.inner_text().strip()
                    if not text:
                        text = elem.get_attribute('aria-label') or elem.get_attribute('title') or ''
                    if text:
                        clickable.append((text, elem))
        # Remove duplicates by text
        seen = set()
        unique_clickable = []
        for text, elem in clickable:
            if text not in seen:
                unique_clickable.append((text, elem))
                seen.add(text)
        clickable = [(i, text, elem) for i, (text, elem) in enumerate(unique_clickable)]
        # Try ordinal
        idx = extract_ordinal(user_input)
        if idx is not None and idx < len(clickable):
            clickable[idx][2].click()
            print(f"Clicked item: {clickable[idx][1]}")
            speak(f"Clicked item {clickable[idx][1]}")
            return
        # Try fuzzy match
        idx, elem = fuzzy_match_title(user_input, clickable)
        if elem:
            elem.click()
            print(f"Clicked item: {clickable[idx][1]}")
            speak(f"Clicked item {clickable[idx][1]}")
            return
        # Fallback: list titles
        print("Could not find a matching item. Here are the top results:")
        speak("I couldn't find a matching item. Here are the top results.")
        for i, text, _ in clickable[:5]:
            print(f"{i+1}: {text}")
            speak(f"Result {i+1}: {text}")
        return

    print("Command not recognized or not supported.")
    speak("Command not recognized or not supported.")

def suggest_clickable_elements(page, clickable=None):
    try:
        if clickable is None:
            clickable = []
            for sel in ['button', 'a']:
                for elem in page.query_selector_all(sel):
                    if elem.is_visible():
                        text = elem.inner_text().strip()
                        if text:
                            clickable.append((text, elem))
        suggestions = [t for t, _ in clickable]
        if suggestions:
            print("Some clickable elements you can try (use 'click #<number>'):")
            for i, s in enumerate(suggestions[:10]):
                print(f"#{i}: {s}")
            page._clickable_suggestions = [elem for _, elem in clickable[:10]]
            speak("Some clickable elements are suggested in the console.")
        else:
            print("No visible clickable elements found.")
            speak("No visible clickable elements found.")
    except Exception as e:
        print(f"Error suggesting clickable elements: {e}")
        speak("Could not suggest clickable elements.")
        save_debug_info(page, "suggest_clickable_elements")

def listen_for_command(recognizer, microphone, overlay, prompt=None):
    """Listen for a voice command and return the recognized text."""
    if prompt:
        print(prompt)
    overlay.set_status("Listening...")
    with microphone as source:
        print("🎤 Listening for your command...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)
    overlay.set_status("Processing...")
    try:
        command = recognizer.recognize_google(audio)
        print(f"🗣️ You said: {command}")
        overlay.set_status("Ready")
        return command
    except sr.UnknownValueError:
        print("❌ Sorry, I did not understand that. Please try again.")
        speak("Sorry, I did not understand that. Please try again.")
        overlay.set_status("Ready")
        return None
    except sr.RequestError as e:
        print(f"❌ Could not request results from Google Speech Recognition service; {e}")
        speak("Could not request results from Google Speech Recognition service. Please try again.")
        overlay.set_status("Ready")
        return None

def click_best_match(page, target):
    global last_search_results
    # Try to find all clickable items (e.g., video titles, product names)
    selectors = [
        'a', 'button', '[role=button]', '[role=link]', '[tabindex="0"]', '[onclick]', '[data-testid]', '[aria-label]'
    ]
    clickable = []
    for sel in selectors:
        for elem in page.query_selector_all(sel):
            if elem.is_visible():
                text = None
                try:
                    text = elem.inner_text().strip()
                except Exception:
                    pass
                if not text:
                    try:
                        text = elem.get_attribute('aria-label') or elem.get_attribute('title') or elem.get_attribute('name') or elem.get_attribute('id')
                    except Exception:
                        text = None
                if text:
                    clickable.append((text, elem))
    last_search_results = clickable
    # Fuzzy match
    texts = [t for t, _ in clickable]
    matches = get_close_matches(target, texts, n=3, cutoff=0.5)
    if not matches:
        print("No matching result found.")
        speak("No matching result found.")
        return False
    if len(matches) == 1:
        idx = texts.index(matches[0])
        elem = clickable[idx][1]
        elem.click()
        print(f"Clicked item: {matches[0]}")
        speak(f"Clicked item: {matches[0]}")
        return True
    # Multiple matches: ask user to pick
    print("Multiple matches found:")
    for i, m in enumerate(matches):
        print(f"{i+1}: {m}")
        speak(f"Option {i+1}: {m}")
    speak("Please say the number of the option you want.")
    # Listen for user choice
    choice = None
    while choice is None:
        user_input = listen_for_command(recognizer, microphone, overlay, prompt="Say the number of your choice.")
        if user_input:
            try:
                num = int(user_input.strip())
                if 1 <= num <= len(matches):
                    choice = num
            except Exception:
                continue
    idx = texts.index(matches[choice-1])
    elem = clickable[idx][1]
    elem.click()
    print(f"Clicked item: {matches[choice-1]}")
    speak(f"Clicked item: {matches[choice-1]}")
    return True

def ai_command_handler(user_command, page, overlay):
    global last_action
    overlay.set_status("Processing...")
    html = page.content()
    context = f"Last action: {last_action}. " if last_action else ""
    prompt = (
        f"You are an AI web automation assistant. {context}Given the following user command and the current page HTML, "
        f"break the command into a list of actionable steps (open, search, click, extract, summarize, etc). "
        f"Only use 'search' if the user explicitly says so. If the user says 'click [something]' after a search, do NOT add a search step, only click a result matching that text. "
        f"For each step, specify the action and the target (e.g., 'search: HTML', 'click: JQ Tutorial', 'summarize', etc). "
        f"Respond in JSON as a list of steps, e.g. [{{'action': 'search', 'target': 'HTML'}}, ...].\n"
        f"User command: {user_command}\n"
        f"HTML:\n{html[:3000]}"
    )
    try:
        import json
        # Always try heuristics first
        try:
            handle_command(page, user_command)
            overlay.set_status("Ready")
            return
        except Exception as heur_e:
            print(f"[Heuristics failed, falling back to AI] {heur_e}")
        # If heuristics fail, use AI plan
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=300,
        )
        ai_content = response.choices[0].message.content.strip()
        try:
            plan = json.loads(ai_content)
        except Exception:
            import re
            match = re.search(r'\[.*\]', ai_content, re.DOTALL)
            if match:
                plan = json.loads(match.group(0))
            else:
                print("AI could not parse plan, giving up.")
                overlay.set_status("Ready")
                return
        if user_command.strip().lower().startswith('click'):
            filtered_plan = [step for step in plan if step.get('action', '').lower() != 'search']
            if not filtered_plan:
                filtered_plan = [{'action': 'click', 'target': user_command.strip()[6:]}]
            plan = filtered_plan
        for i, step in enumerate(plan):
            action = step.get('action', '').lower()
            target = step.get('target', '')
            last_action = action
            performed = False
            try:
                if action in ['open', 'search', 'click', 'type']:
                    handle_command(page, f"{action} {target}")
                    performed = True
                elif action == 'summarize':
                    summarize_page(page, speak_result=False)  # Do not speak
                    performed = True
                elif action == 'extract':
                    extract_info(page, target, speak_result=False)  # Do not speak
                    performed = True
                else:
                    print(f"Unknown action: {action}, skipping.")
                    performed = False
            except Exception as e:
                print(f"[AI fallback failed for {action}] {e}")
                performed = False
            if len(plan) > 1 and i < len(plan) - 1:
                time.sleep(4)
        overlay.set_status("Ready")
    except Exception as e:
        print(f"[AI Command Handler Error] {e}")
        overlay.set_status("Ready")

# Update summarize_page and extract_info to only speak concise results

def summarize_page(page, speak_result=True):
    html = page.content()
    prompt = (
        f"Summarize the main content of this web page in 2-3 sentences.\nHTML:\n{html[:3000]}"
    )
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=150,
        )
        summary = response.choices[0].message.content.strip()
        print(f"Summary: {summary}")
        if speak_result:
            speak(summary)
    except Exception as e:
        print(f"[Summarize Error] {e}")
        if speak_result:
            speak("I could not summarize this page.")

def extract_info(page, target, speak_result=True):
    html = page.content()
    prompt = (
        f"Extract all information about '{target}' from this web page. List any relevant data, links, or facts.\nHTML:\n{html[:3000]}"
    )
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=200,
        )
        info = response.choices[0].message.content.strip()
        print(f"Extracted info: {info}")
        if speak_result:
            speak(info)
    except Exception as e:
        print(f"[Extract Error] {e}")
        if speak_result:
            speak(f"I could not extract information about {target}.")

def bot_main(overlay):
    p, browser, page = setup_playwright()
    try:
        speak("Voice recognition is now active. Please speak your command.")
        while True:
            command = listen_for_command(recognizer, microphone, overlay)
            if not command:
                continue
            if command.strip().lower() in ["exit", "quit", "stop", "bye"]:
                print("Exiting.")
                speak("Exiting.")
                break
            ai_command_handler(command, page, overlay)
            time.sleep(2)  # Small delay to avoid rapid repeated listening
    finally:
        browser.close()
        p.stop()

if __name__ == "__main__":
    overlay = AnimatedOverlay()
    bot_thread = threading.Thread(target=bot_main, args=(overlay,), daemon=True)
    bot_thread.start()
    print("Overlay started!")
    overlay.run()