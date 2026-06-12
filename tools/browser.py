from urllib.parse import quote

import subprocess

from config import BROWSER_ENGINE, DATA_DIR
from playwright.sync_api import sync_playwright

class Browser:
    def __init__(self):
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None
        self._profile_dir = f"{DATA_DIR}/browser_profile"

    def _ensure_started(self):
        if not self._is_page_valid():
            try:
                self.close()
                self._playwright = sync_playwright().start()
                browser_type = getattr(self._playwright, BROWSER_ENGINE, self._playwright.firefox)
                self._context = browser_type.launch_persistent_context(
                    self._profile_dir,
                    headless=False,
                    args=['--no-sandbox', '--disable-setuid-sandbox']
                )
                self._page = self._context.pages[0] if self._context.pages else self._context.new_page()
            except Exception as e:
                print(f"[BROWSER] Failed to start: {e}")
                self.close()
                raise

    def _is_page_valid(self):
        """Check if page is still open and valid"""
        try:
            if self._page and not self._page.is_closed():
                return True
        except:
            pass
        return False

    def navigate(self, url: str) -> str:
        """Navigate to URL with automatic recovery on failure"""
        max_retries = 2
        for attempt in range(max_retries):
            try:
                if not self._is_page_valid():
                    print("[BROWSER] Page closed, restarting...")
                    self.close()
                    self._ensure_started()
                
                self._page.goto(url, wait_until="domcontentloaded", timeout=15000)
                return f"Opened {url}"
            except Exception as e:
                print(f"[BROWSER] Navigation error (attempt {attempt+1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    self.close()
                    self._ensure_started()
                else:
                    self.close()
                    return self._open_system_browser(url)

    def _open_system_browser(self, url: str) -> str:
        for command in (["firefox", url], ["xdg-open", url]):
            try:
                subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return f"Opened {url}"
            except Exception:
                continue
        raise RuntimeError(f"Could not open {url} in a browser")

    def search_web(self, query: str) -> str:
        url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        return self.navigate(url)

    def open_mail(self) -> str:
        return self.navigate("https://mail.google.com")

    def search_mail(self, query: str = "") -> str:
        query = (query or "").strip()
        if not query:
            return self.open_mail()
        return self.navigate(f"https://mail.google.com/mail/u/0/#search/{quote(query)}")

    def read_mail_page(self) -> str:
        self._ensure_started()
        text = self.get_page_text()
        if not text:
            return "I could not read the current mail page."
        return text[:2000]

    def prepare_email(self, to: str = "", subject: str = "", body: str = "") -> str:
        return self._with_browser_recovery(
            lambda: self._prepare_email(to=to, subject=subject, body=body)
        )

    def _prepare_email(self, to: str = "", subject: str = "", body: str = "") -> str:
        self._ensure_started()
        params = []
        if to:
            params.append(f"to={quote(to)}")
        if subject:
            params.append(f"su={quote(subject)}")
        if body:
            params.append(f"body={quote(body)}")

        url = "https://mail.google.com/mail/?view=cm&fs=1"
        if params:
            url += "&" + "&".join(params)
        self._page.goto(url, wait_until="domcontentloaded", timeout=20000)
        return "Prepared the email draft. Please confirm before sending."

    def prepare_whatsapp_message(self, contact: str = "", message: str = "") -> str:
        """Open WhatsApp Web and prepare a message without pressing send."""
        return self._with_browser_recovery(
            lambda: self._prepare_whatsapp_message(contact=contact, message=message)
        )

    def _prepare_whatsapp_message(self, contact: str = "", message: str = "") -> str:
        self._ensure_started()
        contact = (contact or "").strip()
        message = (message or "").strip()

        if self._looks_like_phone(contact):
            phone = "".join(ch for ch in contact if ch.isdigit())
            url = f"https://web.whatsapp.com/send?phone={phone}"
            if message:
                url += f"&text={quote(message)}"
            self._page.goto(url, wait_until="domcontentloaded", timeout=20000)
            return "Prepared WhatsApp message window. Please confirm before sending."

        self._page.goto("https://web.whatsapp.com", wait_until="domcontentloaded", timeout=20000)
        if not contact:
            return "Opened WhatsApp Web. I need the contact name before preparing the message."

        try:
            self._page.wait_for_timeout(2500)
            search_box = self._page.locator(
                "div[contenteditable='true'][data-tab='3'], "
                "div[contenteditable='true'][role='textbox']"
            ).first
            search_box.click(timeout=8000)
            search_box.fill(contact, timeout=8000)
            self._page.wait_for_timeout(1200)
            self._page.get_by_title(contact, exact=False).first.click(timeout=8000)
        except Exception:
            return (
                f"Opened WhatsApp Web. I could not automatically select {contact}, "
                "so please open that chat and tell me the message."
            )

        if not message:
            return f"Opened WhatsApp chat for {contact}. What message should I type?"

        try:
            message_box = self._page.locator(
                "footer div[contenteditable='true'][role='textbox'], "
                "div[contenteditable='true'][data-tab='10']"
            ).first
            message_box.click(timeout=8000)
            message_box.fill(message, timeout=8000)
            return f"Typed the WhatsApp message for {contact}. Please confirm if you want me to send it."
        except Exception:
            return (
                f"Opened WhatsApp chat for {contact}, but I could not type the message automatically."
            )

    def _looks_like_phone(self, value: str) -> bool:
        digits = "".join(ch for ch in value if ch.isdigit())
        return len(digits) >= 8

    def start_whatsapp_call(self, contact: str = "", video: bool = False) -> str:
        """Open a WhatsApp chat and click the voice/video call button."""
        return self._with_browser_recovery(
            lambda: self._start_whatsapp_call(contact=contact, video=video)
        )

    def _start_whatsapp_call(self, contact: str = "", video: bool = False) -> str:
        self._ensure_started()
        contact = (contact or "").strip()
        if not contact:
            return "I need the WhatsApp contact name before starting a call."

        self._page.goto("https://web.whatsapp.com", wait_until="domcontentloaded", timeout=20000)
        try:
            self._page.wait_for_timeout(2500)
            
            # Use WhatsApp Web's native keyboard shortcut to focus the Search box
            self._page.keyboard.press("Control+Alt+/")
            self._page.wait_for_timeout(1000)
            
            # Type the contact name
            self._page.keyboard.type(contact, delay=100)
            self._page.wait_for_timeout(2500) # Wait for search results to populate
            
            # Hit Enter to open the first matched contact chat
            self._page.keyboard.press("Enter")
            self._page.wait_for_timeout(2000)
        except Exception:
            return (
                f"Opened WhatsApp Web, but I could not automatically select {contact}. "
                "Please open that chat and ask me to call again."
            )

        labels = ["Video call"] if video else ["Voice call", "Audio call"]
        for label in labels:
            try:
                self._page.get_by_label(label, exact=False).first.click(timeout=5000)
                call_type = "video call" if video else "voice call"
                return f"Started a WhatsApp {call_type} with {contact}."
            except Exception:
                continue

        try:
            title = "Video call" if video else "Voice call"
            self._page.locator(f"span[data-icon*='{'video' if video else 'call'}']").first.click(timeout=5000)
            return f"Started a WhatsApp {title.lower()} with {contact}."
        except Exception:
            return (
                f"I opened the WhatsApp chat for {contact}, but I could not find the call button."
            )

    def _with_browser_recovery(self, operation):
        last_error = None
        for attempt in range(2):
            try:
                self._ensure_started()
                return operation()
            except Exception as error:
                last_error = error
                message = str(error).lower()
                if "closed" not in message and "target page" not in message:
                    raise
                print(f"[BROWSER] Closed page recovered on attempt {attempt + 1}: {error}")
                self.close()
        raise last_error

    def get_page_text(self) -> str:
        if self._is_page_valid():
            try:
                return self._page.inner_text("body")[:2000]
            except:
                pass
        return ""

    def click_element(self, selector: str) -> str:
        if not self._is_page_valid():
            raise RuntimeError("Page is not open")
        self._page.click(selector)
        return f"Clicked {selector}"

    def close(self):
        """Safely close browser and cleanup"""
        try:
            if self._page:
                try:
                    self._page.close()
                except:
                    pass
                self._page = None
        except:
            pass
        
        try:
            if self._browser:
                self._browser.close()
                self._browser = None
        except:
            pass

        try:
            if self._context:
                self._context.close()
                self._context = None
        except:
            pass
        
        try:
            if self._playwright:
                self._playwright.stop()
                self._playwright = None
        except:
            pass

import threading

_thread_local = threading.local()

def _get_browser():
    if not hasattr(_thread_local, "browser"):
        _thread_local.browser = Browser()
    return _thread_local.browser

def navigate(url: str) -> str:
    return _get_browser().navigate(url)

def search_web(query: str) -> str:
    return _get_browser().search_web(query)

def open_mail() -> str:
    return _get_browser().open_mail()

def search_mail(query: str = "") -> str:
    return _get_browser().search_mail(query=query)

def read_mail_page() -> str:
    return _get_browser().read_mail_page()

def prepare_email(to: str = "", subject: str = "", body: str = "") -> str:
    return _get_browser().prepare_email(to=to, subject=subject, body=body)

def prepare_whatsapp_message(contact: str = "", message: str = "") -> str:
    return _get_browser().prepare_whatsapp_message(contact=contact, message=message)

def start_whatsapp_call(contact: str = "", video: bool = False) -> str:
    return _get_browser().start_whatsapp_call(contact=contact, video=video)

def get_page_text() -> str:
    return _get_browser().get_page_text()
