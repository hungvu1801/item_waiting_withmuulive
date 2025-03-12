import os
import time
import concurrent.futures
import sys
import threading
import queue

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException

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
        # driver.maximize_window()
    except Exception as e:
        print(e)
        return None
    return driver

def wait_for_button(driver, tab_handle, result_queue, stop_event):

    while not stop_event.is_set():
        try:
            driver.switch_to.window(tab_handle)
            # Adjust the XPATH according to your button's location
            time.sleep(5)
            quantity_input = driver.find_element(By.ID, "quantity")
            driver.execute_script("arguments[0].value = '1';", quantity_input)
            button = WebDriverWait(driver, 1).until(
                EC.presence_of_element_located((By.XPATH, "//div[@class='ec-base-button']"))
            )
            driver.execute_script("arguments[0].scrollIntoView({ behavior: 'smooth', block: 'center' });", button)

            button = WebDriverWait(driver, 1).until(
                EC.presence_of_element_located((By.XPATH, "//div[@class='ec-base-button']/a[1][text()='BUY NOW']"))
            )
            # If button found, put result in queue and set stop event
            button.click()

            result_queue.put({
                'tab_handle': tab_handle,
                'url': driver.current_url,
                'status': 'clicked'
            })
            # stop_event.set()
            # break
        except (TimeoutException, NoSuchElementException):
            # Button not found yet, continue monitoring
            continue
        except Exception as e:
            print(f"Error in tab {tab_handle}: {str(e)}")
            break

def wait_for_element(driver, url: str):
    """
    Opens a new tab and navigates to URL
    """
    driver.execute_script("window.open('');")
    driver.switch_to.window(driver.window_handles[-1])
    driver.get(url)
    time.sleep(5)

def main(profile:str=None):
    print(profile)
    driver = open_driver(profile=profile)
    driver.get("https://withmuulive.com/member/login.html")

    _ = input("Press any key to continue... ")

    url_list = [
        "https://withmuulive.com/product/%EC%A7%80%EB%93%9C%EB%9E%98%EA%B3%A4g-dragon-%EA%B3%B5%EC%8B%9D-%EC%9D%91%EC%9B%90%EB%B4%89/151/category/53/display/1/",
        "https://withmuulive.com/product/%EC%A7%80%EB%93%9C%EB%9E%98%EA%B3%A4g-dragon-%EA%B3%B5%EC%8B%9D-%EC%9D%91%EC%9B%90%EB%B4%89-%ED%81%AC%EB%9E%98%EB%93%A4/150/category/53/display/1/",
        "https://withmuulive.com/product/%EC%A7%80%EB%93%9C%EB%9E%98%EA%B3%A4g-dragon-%EA%B3%B5%EC%8B%9D-%EB%AF%B8%EB%8B%88-%EB%9D%BC%EC%9D%B4%ED%8A%B8-%ED%82%A4%EB%A7%81/149/category/53/display/1/",
        "https://withmuulive.com/product/%EC%9C%84%ED%94%BC-%EC%B6%A9%EC%A0%84%EC%8B%9D-%EC%9D%91%EC%9B%90%EB%B4%89-%EB%B0%B0%ED%84%B0%EB%A6%AC/152/category/53/display/1/"]
    
    # Open each URL in a new tab
    for url in url_list:
        wait_for_element(driver, url)
    
    # Create thread-safe queue and event
    result_queue = queue.Queue()
    stop_event = threading.Event()
    threads = []
    
    # Start monitoring each tab
    for handle in driver.window_handles[1:]:  # Skip first tab (login page)
        thread = threading.Thread(
            target=wait_for_button,
            args=(driver, handle, result_queue, stop_event)
        )
        thread.daemon = True  # Thread will close when main program exits
        thread.start()
        threads.append(thread)
    
    try:
        # Keep track of successful clicks
        successful_clicks = []
        
        # Wait for buttons to be clicked (up to 4)
        while len(successful_clicks) < 4:
            try:
                result = result_queue.get()  # 30 second timeout
                successful_clicks.append(result)
                print(f"Button clicked in tab with URL: {result['url']}")
            except queue.Empty:
                print("Timeout reached - no more buttons found")
                break
                
    except Exception as e:
        print(f"Error in main thread: {str(e)}")
    finally:
        stop_event.set()  # Signal all threads to stop
        for thread in threads:
            thread.join(timeout=1)  # Wait for threads to finish
        
        # Print summary of clicks
        print("\nSummary of clicks:")
        for click in successful_clicks:
            print(f"Clicked in: {click['url']}")
        
    input("Press Enter to close browser...")
    driver.quit()

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("Usage: python main.py [profile]")
        quit()
    profile = sys.argv[1]
    main(profile=profile)