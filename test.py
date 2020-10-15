import csv
from datetime import datetime
from datetime import timedelta
from dateutil.parser import parse
import io
import json
import os
from pprint import pprint
import requests
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
# from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
import time as timer


"""
CONSTANTS
"""
CONFIG_PATH = './config.json'
MAX_COMMENT = 235

"""
CONFIGURATION
"""
config = {}
if os.path.isfile(CONFIG_PATH):
    with open(CONFIG_PATH) as config_file:
        config = json.load(config_file)

"""
GLOBALS
"""
headers = {"X-Api-Key": config['clockify']['api']['key']}
create_temp_file = config['gte']['settings'].get('create_temp_file', 0)
gte_debug = config['gte']['settings'].get('debug', 0)
use_browser = config.get('use_browser', 1)
wk_type = config['gte']['global']['Type']
wk_site = config['gte']['global']['Site']
wk_loc = config['gte']['global']['Location']
sleep_seconds_between_ops = 0.1 if not gte_debug else 1
page_wait_for_rows = 2 * sleep_seconds_between_ops
delay = 20
input_delay = 60


def get_start_end_week(seed_date):
    starter = parse(seed_date)
    start_week = starter - timedelta(days=(starter.weekday()))
    start_week = start_week.replace(hour=0, minute=0, second=0, microsecond=0)
    end_week = start_week + timedelta(days=7) - timedelta(seconds=1)

    return start_week, end_week


def login():
    user = config['gte']['credentials']['user']
    driver.get("https://upp.capgemini.com/")
    try:
        elem = WebDriverWait(driver, delay).until(expected_conditions.presence_of_element_located((By.ID, 'login')))
        elem.send_keys(user)
        elem = WebDriverWait(driver, delay).until(expected_conditions.presence_of_element_located((By.ID, 'passwd')))
        elem.click()
        print("IN BROWSER: Please enter your MobilePass code and click 'Log On' button to proceed...")
    except TimeoutException:
        print("Loading took too much time!")

    try:
        ssourl = expected_conditions.url_contains("sspoam.capgemini.com")
        WebDriverWait(driver, input_delay).until(ssourl)
    except TimeoutException:
        print("Timed out waiting for SSO url")
        raise NameError("SSO timeout")

    btn = driver.find_element_by_css_selector("body > button:nth-child(2)")
    btn.click()

    try:
        ec = expected_conditions.title_contains("Oracle Access Management")
        WebDriverWait(driver, delay).until(ec)
    except TimeoutException:
        print("Timed out waiting on Oracle login page")
        raise NameError("No oracle login page")

    elem = driver.find_element_by_xpath("//*[@id=\"username\"]")
    elem.send_keys(user)
    elem = driver.find_element_by_xpath("//*[@id=\"password\"]")
    elem.click()
    print("IN BROWSER: Please enter your Capgemini password and click 'Login' button to proceed...")

    try:
        ec = expected_conditions.url_contains("upp.capgemini.com/OA_HTML")
        WebDriverWait(driver, input_delay).until(ec)
    except TimeoutException:
        print("Timed out waiting on GTE main page")
        raise NameError("No GTE main page page")

    driver.get("https://upp.capgemini.com/OA_HTML/RF.jsp?function_id=11644")


"""
MAIN
"""
# Setup dates for report
if config.get("use_week"):
    default_date = config["use_week"]
else:
    default_date = datetime.now().date()
    start_of_week, end_of_week = get_start_end_week(str(default_date))

    print("\n\nClockify to GTE")
    print("---------------------------------------------------")
    print("Enter a date in the week to use (format YYYY-MM-DD)")
    default_date = input("<ENTER> for default range ({} - {}): ".format(
        start_of_week.date(),
        end_of_week.date())
    ) or start_of_week.date()

start_of_week, end_of_week = get_start_end_week(str(default_date))
print(
    "Using date {}, report will be from {} to {}".format(
        default_date,
        start_of_week,
        end_of_week
    )
)

driver = webdriver.Firefox()
driver.set_window_size(1600, 900)
# login()
driver.get("file://{}/htestml/recentTimecards.html".format(os.getcwd()))
finddate = start_of_week.strftime('%d-%b-%Y')
xpath = "//table[@id='Hxctcarecentlist:Content']//tr[td//text()='Working' and td//text()='{}']".format(finddate)
elems = driver.find_elements_by_xpath(xpath)
if len(elems) == 0:
    # must create a new timecard
    pass
else:
    # found the right timecard in the "Working" status for this start date
    elem = elems[0].find_element_by_xpath(".//a[contains(@id, 'Hxctcarecentlist:UpdEnable')]")
    elem.click()

print("hay")
