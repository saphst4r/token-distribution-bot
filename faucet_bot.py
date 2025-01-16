import os
import time
from dotenv import load_dotenv
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

# Load environment variables
load_dotenv()

class FaucetBot:
    def __init__(self):
        self.wallet_address = os.getenv('WALLET_ADDRESS')
        self.faucet_url = "https://app.buildonhybrid.com/faucet"
        
    def setup_browser(self):
        options = uc.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')
        
        # Force the Chrome version to match your installed version
        version_main = 131
        
        try:
            self.driver = uc.Chrome(
                options=options,
                version_main=version_main,
                driver_executable_path=None
            )
            self.driver.set_window_size(1920, 1080)
        except Exception as e:
            print(f"Error initializing Chrome: {e}")
            raise
            
    def request_tokens(self):
        try:
            print("Navigating to faucet URL...")
            self.driver.get(self.faucet_url)
            
            # Wait for page to load and find the wallet input field
            print("Waiting for wallet input field...")
            wallet_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[placeholder="Input your HYB address..."]'))
            )
            
            # Input wallet address
            print("Entering wallet address...")
            wallet_input.clear()
            wallet_input.send_keys(self.wallet_address)
            
            # Find and click the Send Tokens button
            print("Looking for Send Tokens button...")
            send_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Send Tokens')]"))
            )
            
            print("Clicking Send Tokens button...")
            send_button.click()
            
            # Wait for some time to see if the request was successful
            print("Waiting for request to complete...")
            time.sleep(5)
            
            # Try to find success or error messages
            try:
                messages = self.driver.find_elements(By.CSS_SELECTOR, ".Toastify__toast-body")
                if messages:
                    for msg in messages:
                        print(f"Message received: {msg.text}")
            except:
                print("No toast messages found")
                
        except Exception as e:
            print(f"Error during token request: {str(e)}")
            print("Current URL:", self.driver.current_url)
            
    def run(self):
        try:
            print("Setting up browser...")
            self.setup_browser()
            
            print("Requesting tokens...")
            self.request_tokens()
            
        except Exception as e:
            print(f"Error: {e}")
        finally:
            if hasattr(self, 'driver'):
                self.driver.quit()

if __name__ == "__main__":
    bot = FaucetBot()
    bot.run() 