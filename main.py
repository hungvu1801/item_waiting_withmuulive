import os
import time
# import concurrent.futures
import sys
# import threading
# import queue

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException, WebDriverException
# from urllib3.exceptions import MaxRetryError, ProtocolError

def open_driver(headless:bool=False, profile:str=None, debug_port:int=None):
    """
    Docstring:
    
    """

    options = webdriver.ChromeOptions()
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"

    try:
        service = Service(ChromeDriverManager().install())
        #### if using capture program, use these options ####

        options.add_argument("--window-size=1920,1080")
        profile_path = os.path.join(os.getcwd(), f"user_profiles/profile_{profile}")
        options.add_argument(f"user-data-dir={profile_path}")

        driver = webdriver.Chrome(service=service, options=options)
        if debug_port:
            options.add_argument(f'--remote-debugging-port={debug_port}')
            options.add_experimental_option("debuggerAddress", f"127.0.0.1:{debug_port}")
            #####################################################
        driver.execute_cdp_cmd("Network.setUserAgentOverride", {"userAgent": user_agent})
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        # driver.maximize_window()
    except Exception as e:
        print(e)
        return None
    return driver

def wait_for_button(driver, tab_handle):
    try:            
        driver.switch_to.window(tab_handle)

        driver.refresh()
        quantity_input = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, "quantity"))
            )
        driver.execute_script("arguments[0].value = '1';", quantity_input)
        buy_button = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "//div[@class='ec-base-button']/a[1][text()='BUY NOw']"))
        )
        
        buy_button.click()
        print(f"Successfully clicked BUY NOW: checkout url {driver.current_url}")

        return True

    except (TimeoutException, NoSuchElementException, StaleElementReferenceException):
        # print(f"Error in tab {tab_handle}: {str(e)}")
        return False
    except Exception as e:
        print(f"Error: {str(e)}")
        return False


def wait_for_element(driver, url: str):
    """
    Opens a new tab and navigates to URL
    """
    driver.execute_script("window.open('');")
    driver.switch_to.window(driver.window_handles[-1])
    driver.get(url)

    buy_button = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located(
            (By.XPATH, "//div[@class='ec-base-button']"))
    )
    driver.execute_script("arguments[0].scrollIntoView({ behavior: 'smooth', block: 'center' });", buy_button)

    time.sleep(2)

def main(profile:str=None):
    print(profile)
    driver = open_driver(profile=profile)
    driver.get("https://withmuulive.com/member/login.html")

    input("\nPress any key to continue after logging in... \n")

    url_list = [
        "https://withmuulive.com/product/%EC%A7%80%EB%93%9C%EB%9E%98%EA%B3%A4g-dragon-%EA%B3%B5%EC%8B%9D-%EC%9D%91%EC%9B%90%EB%B4%89/151/category/53/display/1/",
        "https://withmuulive.com/product/%EC%A7%80%EB%93%9C%EB%9E%98%EA%B3%A4g-dragon-%EA%B3%B5%EC%8B%9D-%EC%9D%91%EC%9B%90%EB%B4%89-%ED%81%AC%EB%9E%98%EB%93%A4/150/category/53/display/1/",
        "https://withmuulive.com/product/%EC%A7%80%EB%93%9C%EB%9E%98%EA%B3%A4g-dragon-%EA%B3%B5%EC%8B%9D-%EB%AF%B8%EB%8B%88-%EB%9D%BC%EC%9D%B4%ED%8A%B8-%ED%82%A4%EB%A7%81/149/category/53/display/1/",
        "https://withmuulive.com/product/%EC%9C%84%ED%94%BC-%EC%B6%A9%EC%A0%84%EC%8B%9D-%EC%9D%91%EC%9B%90%EB%B4%89-%EB%B0%B0%ED%84%B0%EB%A6%AC/152/category/53/display/1/"]
    
    # Open each URL in a new tab
    for url in url_list:
        wait_for_element(driver, url)

    successful_clicks = set()  # Use set to track unique successful clicks
    tab_handles = driver.window_handles[1:]
        # Wait for buttons to be clicked (up to 4)
    while len(successful_clicks) < len(tab_handles):
        for handle in tab_handles:
            if handle not in successful_clicks:  # Only check tabs that haven't been clicked
                if wait_for_button(driver, handle):
                    successful_clicks.add(handle)
                    print(f"\nSuccessful clicks so far: {len(successful_clicks)}/{len(tab_handles)}")
        
        # Optional: Add a small delay between cycles
        time.sleep(1)

    print("\nAll buttons clicked successfully!")
    print("\nSummary of clicks:")
    for handle in successful_clicks:
        driver.switch_to.window(handle)
        print(f"Clicked in: {driver.current_url}")
    input("Press Enter to close browser...")
    driver.quit()

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("Usage: python main.py [profile]")
        quit()
    profile = sys.argv[1]
    main(profile=profile)