import csv
from datetime import datetime
from datetime import timedelta
from dateutil.parser import parse
import getpass
import io
import json
import os
import requests
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
import time as timer


"""
CONSTANTS
"""
CONFIG_PATH = './config.json'
TOTAL_PATH = '__TOTALS'

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
use_browser = config.get('use_browser', 1)
wk_type = config['gte']['global']['Type']
wk_site = config['gte']['global']['Site']
wk_loc = config['gte']['global']['Location']
sleep_seconds_between_ops = 1.2
page_wait_for_rows = 2 * sleep_seconds_between_ops
totals = [0] * 7

"""
FUNCTIONS AND METHODS
"""


def auto_input_data(driver, timesheet_entries):
    row = 0
    for key in timesheet_entries:
        row += 1
        codes = key.split('|')
        project = codes[0]
        task = codes[1]
        data = timesheet_entries[key]
        auto_input_row(driver, row, project, task, data)
        #elem = driver.find_element_by_xpath(get_gte_element('Project Details', row))
        #elem.send_keys(timesheet_entry[''])
        #webdriver.ActionChains(driver).send_keys(Keys.TAB).perform()
        #timer.sleep(30)


def auto_input_row(driver, row, project, task, data):
    te = data['time']
    comments = data['comments']
    print(
        "({}) {} - {} : {} : {} : {} | {} | {} | {} | {} | {} | {} | {}".format(
            row,
            project,
            task,
            wk_type,
            wk_site,
            wk_loc,
            te[0],
            te[1],
            te[2],
            te[3],
            te[4],
            te[5],
            te[6]
        )
    )

def accumulate_hours(timesheet_entry, entries):
    bucket = timesheet_entry['Project'].split()[0] + '|' + timesheet_entry['Task']
    # get the data for the bucket or if none, return empty/initialized data
    data = entries.get(bucket, {'time': [0] * 7, 'comments': [''] * 7})
    day_of_week = parse(timesheet_entry['Start Date']).weekday()
    # TIME SECTION
    time_entry = float(timesheet_entry['Duration (decimal)'])
    data['time'][day_of_week] += time_entry
    totals[day_of_week] += time_entry
    # COMMENTS SECTION
    # text hours for the comment entry
    day_hours = timesheet_entry['Duration (h)'].split(':')
    new_comment = "{}:{} - {}".format(
        str(int(day_hours[0])),
        day_hours[1],
        timesheet_entry['Description']
    )
    comments = data['comments'][day_of_week]
    if len(comments) == 0:
        new_comments = new_comment
    else:
        new_comments = "\n".join((comments, new_comment))
    data['comments'][day_of_week] = new_comments
    entries[bucket] = data

    return entries


def clockify_api_request(end, start):
    payload = {
        "dateRangeStart": start.isoformat() + 'Z',
        "dateRangeEnd": end.isoformat() + 'Z',
        "detailedFilter": {
            "page": 1,
            "pageSize": 50,
            "sortColumn": "DATE"
        },
        "exportType": "CSV",
        "users": {
            "ids": ["{}".format(config['clockify']['user_id'])],
            "contains": "CONTAINS",
            "status": "ALL"
        }
    }
    url = (config['clockify']['report']['url'] +
           config['clockify']['report']['detail_uri'].
           format(config['clockify']['workspace_id']))
    resp = requests.post(url=url, json=payload, headers=headers)

    return resp


def get_gte_element(name, row):
    # map of relevant xpath keys we are targeting
    gte_xpath_map = {
        "Period": '//*[@id="N77"]',
        "Project Details": '//*[@id="A24{}N1display"]',
        "Task Details": '//*[@id="A25{}N1display"]',
        "Type": '//*[@id="A26{}N1display"]',
        "Site": '//*[@id="A27{}N1"]',
        "Location": '//*[@id="A28{}N1display"]',
        "Approver": '//*[@id="A37{}N1"]',
        "Monday": '//*[@id="B22_{}_0"]',
        "Tuesday": '//*[@id="B22_{}_1"]',
        "Wednesday": '//*[@id="B22_{}_2"]',
        "Thursday": '//*[@id="B22_{}_3"]',
        "Friday": '//*[@id="B22_{}_4"]',
        "Saturday": '//*[@id="B22_{}_5"]',
        "Sunday": '//*[@id="B22_{}_6"]',
        "Add Another Row": "/html/body/div[5]/form/span[2]/div[3]/div/div[1]/div/div[3]/div[1]/div[2]/span[1]/span/table[1]/tbody/tr/td/table[2]/tbody/tr[5]/td/table/tbody/tr[6]/td[2]/table/tbody/tr[3]/td[1]/table/tbody/tr/td[1]/button"
    }

    return gte_xpath_map.get(name).format(str(row))


def get_start_end_week(seed):
    starter = parse(seed)
    day_of_week = starter.weekday()
    start_week = starter - timedelta(days=day_of_week)
    start_week = start_week.replace(hour=0, minute=0, second=0, microsecond=0)
    end_week = start_week + timedelta(days=7) - timedelta(seconds=1)

    return start_week, end_week


def get_timesheet_from_clockify(start, end):
    resp = clockify_api_request(end, start)
    entries = []

    if create_temp_file:
        stream = open('workfile.csv', mode='w+')
        stream.write(resp.text)
        stream.seek(0)
    else:
        stream = io.StringIO(resp.text)

    reader = csv.DictReader(stream)
    for row in reader:
        entries.append(row)
    stream.close()

    return entries


def login(driver):
    user = config['gte']['credentials']['user']
    delay = 20
    input_delay = 40

    driver.get("https://upp.capgemini.com/")
    try:
        elem = WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.ID, 'login')))
        elem.send_keys(user)
        elem = WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.ID, 'passwd')))
        elem.click()
        print("IN BROWSER: Please enter your MobilePass code and click 'Log On' button to proceed...")
    except TimeoutException:
        print("Loading took too much time!")

    try:
        ssourl = EC.url_contains("sspoam.capgemini.com")
        WebDriverWait(driver, input_delay).until(ssourl)
    except TimeoutException:
        print("Timed out waiting for SSO url")
        raise NameError("SSO timeout")

    btn = driver.find_element_by_css_selector("body > button:nth-child(2)")
    btn.click()

    try:
        ec = EC.title_contains("Oracle Access Management")
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
        ec = EC.url_contains("upp.capgemini.com/OA_HTML")
        WebDriverWait(driver, input_delay).until(ec)
    except TimeoutException:
        print("Timed out waiting on GTE main page")
        raise NameError("No GTE main page page")

    driver.get(
        "https://upp.capgemini.com/OA_HTML/RF.jsp?function_id=16744&resp_id=71369&resp_appl_id=809&security_group_id=0&lang_code=US&oas=ZyZNPnozfgJIWQBaFio13Q..&params=avwQ4Zpumqk4wM2hnLSEtfVRURgrCch9rnGvV9mMQIc")


def make_rows_in_timesheet(param):

    pass


def pull_clockify_info():
    resp = requests.get(
        url=config['clockify']['api']['url'] + "/user",
        headers=headers
    )
    user = resp.json()
    config['clockify']['user_id'] = user['id']
    config['clockify']['workspace_id'] = user['defaultWorkspace']
def transform_data(incoming_timesheet):
    entries = {}
    for timesheet_entry in incoming_timesheet:
        entries = accumulate_hours(
            timesheet_entry,
            entries
        )

    return entries
"""
MAIN
"""
# Setup dates for report

pull_clockify_info()
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

# get range of entries from Clockify
debug_timesheet_entries = get_timesheet_from_clockify(start=start_of_week, end=end_of_week)
# arrange those entries in the most efficient way to enter the data into GTE
reconfigured_timesheets = transform_data(debug_timesheet_entries)

if use_browser:
    # startup the browser
    uber_driver = webdriver.Firefox()

    uber_driver.set_window_size(1400, 700)
    # let's get logged into the application

    login(uber_driver)
    # check to see if timesheet already used/has values


    if (
        uber_driver.find_element_by_xpath('//*[@id="B22_1_0"]').get_attribute('value') or
        uber_driver.find_element_by_xpath('//*[@id="B22_1_1"]').get_attribute('value') or
        uber_driver.find_element_by_xpath('//*[@id="B22_1_2"]').get_attribute('value') or
        uber_driver.find_element_by_xpath('//*[@id="B22_1_3"]').get_attribute('value') or
        uber_driver.find_element_by_xpath('//*[@id="B22_1_4"]').get_attribute('value') or
        uber_driver.find_element_by_xpath('//*[@id="B22_1_5"]').get_attribute('value') or
        uber_driver.find_element_by_xpath('//*[@id="B22_1_6"]').get_attribute('value')
    ):
        raise ValueError("Warning!  Detected an already saved timesheet, not proceeding.")
else:
    uber_driver = None

auto_input_data(uber_driver, reconfigured_timesheets)

print("Hours are at: {}".format(sum(totals)))
