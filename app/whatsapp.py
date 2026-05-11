"""WhatsApp Web automation module."""
import asyncio
import base64
import json
import os
import time
from pathlib import Path
from typing import Optional, List, Dict, Any
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from app.config import CHROME_OPTIONS, WHATSAPP_SESSION_FILE
from app.database import app_state


class WhatsAppClient:
    """WhatsApp Web client."""
    
    BASE_URL = "https://web.whatsapp.com"
    
    def __init__(self):
        self.driver: Optional[webdriver.Chrome] = None
        self._session_loaded = False
    
    async def init_driver(self):
        """Initialize Chrome driver."""
        options = Options()
        for option in CHROME_OPTIONS:
            options.add_argument(option)
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
        except Exception as e:
            print(f"Failed to initialize Chrome driver: {e}")
            # Fallback: try without service
            self.driver = webdriver.Chrome(options=options)
    
    async def close_driver(self):
        """Close the driver."""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
    
    async def load_session(self) -> bool:
        """Load saved session or return False."""
        if self._session_loaded:
            return True
        
        if not WHATSAPP_SESSION_FILE.exists():
            return False
        
        try:
            await self.init_driver()
            self.driver.get(self.BASE_URL)
            
            # Try to load session cookies
            with open(WHATSAPP_SESSION_FILE, 'r') as f:
                session_data = json.load(f)
            
            # Navigate to WhatsApp Web
            self.driver.get(self.BASE_URL)
            
            # Wait for page to load
            await asyncio.sleep(3)
            
            # Check if already authenticated
            if await self.check_authenticated():
                app_state.is_authenticated = True
                self._session_loaded = True
                return True
            
            return False
        except Exception as e:
            print(f"Failed to load session: {e}")
            return False
    
    async def check_authenticated(self) -> bool:
        """Check if authenticated to WhatsApp."""
        if not self.driver:
            return False
        
        try:
            # Check for elements that appear when logged in
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]'))
            )
            app_state.is_authenticated = True
            return True
        except:
            app_state.is_authenticated = False
            return False
    
    async def get_qr_code(self) -> Optional[str]:
        """Get QR code for scanning."""
        if app_state.is_authenticated:
            return None
        
        try:
            if not self.driver:
                await self.init_driver()
            
            # Go to WhatsApp Web
            self.driver.get(self.BASE_URL)
            
            # Wait for QR code to appear
            wait = WebDriverWait(self.driver, 30)
            qr_container = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-qr-code="true"]'))
            )
            
            # Get QR code image
            qr_canvas = self.driver.find_element(By.CSS_SELECTOR, 'canvas')
            
            # Take screenshot of QR code area
            qr_code_data = qr_canvas.screenshot_as_base64
            
            # Save QR code
            app_state.qr_code = qr_code_data
            
            return qr_code_data
        except Exception as e:
            print(f"Failed to get QR code: {e}")
            return None
    
    async def wait_for_auth(self, timeout: int = 120) -> bool:
        """Wait for QR code scan to complete."""
        if not self.driver:
            return False
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if await self.check_authenticated():
                await self.save_session()
                return True
            await asyncio.sleep(2)
        
        return False
    
    async def save_session(self) -> bool:
        """Save current session."""
        if not self.driver:
            return False
        
        try:
            # Save cookies
            cookies = self.driver.get_cookies()
            with open(WHATSAPP_SESSION_FILE, 'w') as f:
                json.dump(cookies, f)
            
            # Save local storage
            local_storage = self.driver.execute_script("return JSON.stringify(localStorage);")
            session_data = {}
            if WHATSAPP_SESSION_FILE.exists():
                with open(WHATSAPP_SESSION_FILE, 'r') as f:
                    session_data = json.load(f)
            
            session_data['localStorage'] = json.loads(local_storage)
            
            with open(WHATSAPP_SESSION_FILE, 'w') as f:
                json.dump(session_data, f)
            
            return True
        except Exception as e:
            print(f"Failed to save session: {e}")
            return False
    
    async def is_connected(self) -> bool:
        """Check if still connected."""
        return await self.check_authenticated()
    
    async def refresh_contacts(self) -> List[Dict[str, Any]]:
        """Refresh and return contacts list."""
        if not self.driver:
            return []
        
        try:
            # Wait for contacts to load
            wait = WebDriverWait(self.driver, 10)
            contacts_container = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div#pane-side'))
            )
            
            # Find all contacts
            contacts = self.driver.find_elements(
                By.CSS_SELECTOR, 
                'div#pane-side div[role="row"][data-testid="prison-row-name"]'
            )
            
            contacts_list = []
            seen_phones = set()
            
            for contact in contacts[:50]:  # Limit to 50 contacts
                try:
                    name_elem = contact.find_element(By.CSS_SELECTOR, 'span[data-testid="contact-name"]')
                    name = name_elem.text if name_elem else "Unknown"
                    
                    # Click to see phone number
                    contact.click()
                    await asyncio.sleep(0.5)
                    
                    # Try to get phone from header
                    try:
                        header = self.driver.find_element(By.CSS_SELECTOR, 'header')
                        phone = header.text.split('\n')[-1] if header else ""
                    except:
                        phone = ""
                    
                    if phone and phone not in seen_phones:
                        seen_phones.add(phone)
                        contacts_list.append({
                            "phone": phone,
                            "name": name,
                            "avatar": None
                        })
                except:
                    continue
            
            app_state.contacts_cache = contacts_list
            return contacts_list
        except Exception as e:
            print(f"Failed to refresh contacts: {e}")
            return []
    
    async def send_message(self, phone: str, message: str) -> bool:
        """Send a message to a phone number."""
        if not self.driver:
            return False
        
        try:
            # Navigate to the chat
            url = f"{self.BASE_URL}/send?phone={phone}"
            self.driver.get(url)
            
            # Wait for chat to load
            await asyncio.sleep(2)
            
            # Find message input
            wait = WebDriverWait(self.driver, 15)
            message_input = wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]')
                )
            )
            
            # Type message
            message_input.clear()
            message_input.send_keys(message)
            
            # Find send button
            send_button = self.driver.find_element(
                By.CSS_SELECTOR, 
                'button[data-testid="compose-btn-send"]'
            )
            send_button.click()
            
            # Wait for message to send
            await asyncio.sleep(1)
            
            return True
        except Exception as e:
            print(f"Failed to send message: {e}")
            return False
    
    async def send_message_to_name(self, name: str, message: str) -> bool:
        """Send a message by contact name."""
        if not self.driver:
            return False
        
        try:
            # Search for contact
            search_box = self.driver.find_element(By.CSS_SELECTOR, 'div[data-testid="search"] input')
            search_box.clear()
            search_box.send_keys(name)
            
            await asyncio.sleep(1)
            
            # Click on first result
            first_result = self.driver.find_element(
                By.CSS_SELECTOR, 
                'div[data-testid="search-results"] div[role="row"]:first-child'
            )
            first_result.click()
            
            await asyncio.sleep(1)
            
            # Type and send message
            message_input = self.driver.find_element(
                By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]'
            )
            message_input.send_keys(message)
            
            send_button = self.driver.find_element(
                By.CSS_SELECTOR, 
                'button[data-testid="compose-btn-send"]'
            )
            send_button.click()
            
            return True
        except Exception as e:
            print(f"Failed to send message to name: {e}")
            return False


# Global client instance
whatsapp_client = WhatsAppClient()


async def initialize_client():
    """Initialize WhatsApp client with saved session."""
    await whatsapp_client.load_session()


async def close_client():
    """Close WhatsApp client."""
    await whatsapp_client.close_driver()