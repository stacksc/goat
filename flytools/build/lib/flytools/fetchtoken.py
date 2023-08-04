import os, sys , io, shutil
from contextlib import redirect_stdout
# the rest is for selenium bearer token fetch in a headless browser
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.webelement import WebElement

def initialize_webdriver():
    s = ''
    e = ''
    if not shutil.which('chromedriver'):
        captured_stdout = io.StringIO()
        with redirect_stdout(captured_stdout):
            s = Service(ChromeDriverManager().install())
    else:
        captured_stdout = io.StringIO()
        with redirect_stdout(captured_stdout):
            e = shutil.which('chromedriver').strip()
            s = Service(e)
    chrome_options = Options()
    chrome_options.headless = True
    chrome_options.incognito = True
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-software-rasterizer")
    chrome_options.add_argument("--disable-gpu")
    if not s:
        return webdriver.Chrome(service=e, options=chrome_options)
    else:
        return webdriver.Chrome(service=s, options=chrome_options)

def select_ldap(driver):
    auth_buttons = driver.find_elements(By.CLASS_NAME, 'dex-btn-icon--ldap')
    assert auth_buttons, "Unable to locate the LDAP Button"
    auth_buttons[0].click()

def do_login(driver, concourse_user, concourse_password):
    login = driver.find_element(By.ID, 'login')
    assert login is not None, "Unable to locate the 'login' field"
    assert isinstance(login, WebElement), "login: Unexpected Element Type"
    login.send_keys(concourse_user)

    password = driver.find_element(By.ID, 'password')
    assert password is not None, "Unable to locate the 'password' field"
    assert isinstance(password, WebElement), "password: Unexpected Element Type"
    password.send_keys(concourse_password, Keys.ENTER)

def expect_dashbaord(driver):
    driver.find_element(By.XPATH, '/html/head/title')
    assert driver.title == "Dashboard - Concourse", \
    "Dashboard not found.  Login may have been unsuccessful"

def extract_cookie(driver, cookie_name):
    cookies_list = driver.get_cookies()
    cookies_dict = {}
    for cookie in cookies_list:
        cookies_dict[cookie['name']] = cookie['value']
    bearer_token = cookies_dict.get(cookie_name)
    assert bearer_token is not None, "Unable to locate a cookie named: " + cookie_name
    return bearer_token

def fetch_bearer_token(concourse_url, concourse_user, concourse_password):
    driver = initialize_webdriver()
    driver.get(concourse_url)
    driver.implicitly_wait(10) # seconds; but finish sooner if element is available
    select_ldap(driver)
    do_login(driver, concourse_user, concourse_password)
    expect_dashbaord(driver)
    cookie = extract_cookie(driver, "skymarshal_auth").strip('\"').replace('Bearer ', '')
    driver.stop_client()
    driver.close()
    return cookie

def tearDown(driver):
    driver.stop_client()
    driver.close()

def run(concourse_url="https://runway-ci.eng.vmware.com", concourse_user=None, concourse_password=None):
    TOKEN = None
    if concourse_user is not None and concourse_password is not None:
        assert concourse_url
        assert concourse_user
        assert concourse_password
        TOKEN = fetch_bearer_token(concourse_url + "/login", concourse_user, concourse_password)
    return TOKEN.replace("bearer ",'')
