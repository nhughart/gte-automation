import csv
from datetime import datetime
from datetime import timedelta
from dateutil.parser import parse
import io
import json
import os
import requests
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
import time as timer
import yaml
from yaml import parser


"""
CONSTANTS
"""
# CONFIG_SCHEMA can be 'yml' or 'json'
CONFIG_SCHEMA = 'yml'
CONFIG_PATH = './config.{}'.format(CONFIG_SCHEMA)
MAX_COMMENT = 235

"""
CONFIGURATION
"""
config = {}
try:
    with open(CONFIG_PATH) as config_file:
        if CONFIG_SCHEMA == 'yml':
            config = yaml.safe_load(config_file)
        elif CONFIG_SCHEMA == 'json':
            config = json.load(config_file)
except FileNotFoundError:
    print("It appears you don't have a config file: {}".format(CONFIG_PATH))
    print("You can create one using the {} file provided and reading CONFIG.md".format(
        CONFIG_PATH.replace('config', 'config.sample')
    ))
    quit(1)
except (yaml.parser.ParserError, json.decoder.JSONDecodeError):
    print("INVALID {} config file: {}".format(CONFIG_SCHEMA.upper(), CONFIG_PATH))
    print("Please fix the problem with the file...")
    quit(1)

"""
GLOBALS
"""
headers = {"X-Api-Key": config['clockify']['api']['key']}
create_temp_file = config['clockify'].get('create_temp_file', 0)
gte_debug = config['gte']['settings'].get('debug', 0)
check_timesheet_date = config['gte']['settings'].get('check_timesheet_date', True)
use_browser = config.get('use_browser', 1)
wk_type = config['gte']['global']['type']
wk_site = config['gte']['global']['site']
wk_loc = config['gte']['global']['location']
mini_pause = 0.1
sleep_seconds_between_ops = mini_pause if gte_debug else 1.3
xhr_sleep = 2 * sleep_seconds_between_ops
page_wait_for_rows = 3 * sleep_seconds_between_ops
delay = 20
input_delay = 60

totals = [0] * 7

"""
FUNCTIONS AND METHODS
"""


def auto_input_data(timesheet_entries):
    row = 0
    print("{} Rows - Working on:".format(len(timesheet_entries)))
    for index, (key, timesheet_entry) in enumerate(timesheet_entries.items()):
        # prepare for this row "header info"
        row += 1
        project, task, mapped_name = get_mapped_project_task(key)
        name = timesheet_entry.get('name', mapped_name)
        print("Row: {} - {}/{} - {}".format(str(row), project, task, name))
        fill_in_fields(row, 'Project Details', project, xhr_sleep)
        if task == '':
            print("Incoming data has a missing task / default mapping: {}".format(project))
            input("Empty task - please fill this in.  Hit <ENTER> to continue: ")
        else:
            fill_in_fields(row, 'Task Details', task, sleep_seconds_between_ops)
        fill_in_fields(row, 'Type', wk_type, sleep_seconds_between_ops)
        choice_fields(row, 'Site', wk_site, sleep_seconds_between_ops)
        fill_in_fields(row, 'Location', wk_loc, sleep_seconds_between_ops)

        # prepare and enter the days or "detail info"
        time_entries = timesheet_entry['time']
        for day_of_week, time in enumerate(time_entries):
            if time > 0.0:
                fill_in_fields(row, day_of_week, time, mini_pause)

        # Now for the comments
        comments = timesheet_entry['comments']
        fill_in_comments(row, comments)
        timer.sleep(page_wait_for_rows)
    # now, we should save the page.  BUT DON'T SUBMIT - make the user do that
    elem = find_button('Save')
    elem.click()
    timer.sleep(page_wait_for_rows)


def accumulate_hours(timesheet_entry, entries):
    project_info = timesheet_entry['Project'].split('-')
    task = timesheet_entry['Task']
    bucket = project_info[0].strip() + '|' + task
    project, task, mapped_name = get_mapped_project_task(bucket)
    bucket = project + '|' + str(task)
#    name = timesheet_entry.get('name', mapped_name)
#    print("Row: {} - {}/{} - {}".format(str(row), project, task, name))
#    fill_in_fields(row, 'Project Details', project, xhr_sleep)

#    if task == '':
#        project, task, _ = get_mapped_project_task(bucket)
#        bucket = project + '|' + task
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
    data['name'] = project_info[1].strip()

    return entries


def choice_fields(row, field, value, nap):
    # get reference to element based on lookup of the field
    # NOTE: if field passed as an int, it is referencing one of the days of week
    select = Select(driver.find_element_by_xpath(get_gte_element(field, row)))
    # choose the value
    select.select_by_visible_text(str(value))
    webdriver.ActionChains(driver).send_keys(Keys.TAB).perform()
    # nap time to allow for some XHR to happen
    timer.sleep(nap)


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
           config['clockify']['report']['detail_uri'].format(config['clockify']['workspace_id']))
    resp = requests.post(url=url, json=payload, headers=headers)

    return resp


def fill_in_comments(row, comments):
    details_image = 'detailsicon_enabled.gif'
    details = driver.find_elements_by_xpath("//img[contains(@src, '" + details_image + "')]")
    # the row is X, but due to 0-based indexing, first return is index 0
    det = details[row - 1]
    det.click()
    try:
        WebDriverWait(driver, delay).until(
            expected_conditions.presence_of_element_located(
                (
                    By.XPATH, "//button[contains(@title, 'Apply:')]"
                )
            )
        )
    except TimeoutException:
        print("Bucket comment page took too long to load!")

    for day_of_week, comment in enumerate(comments):
        sc = comment.strip()
        if len(sc) > 0:
            trimmed_comment = (sc[:MAX_COMMENT] + '...') if len(sc) > MAX_COMMENT else sc
            elem = driver.find_element_by_xpath(get_gte_comment_element(day_of_week))
            elem.send_keys(trimmed_comment)
            webdriver.ActionChains(driver).send_keys(Keys.TAB).perform()

    find_button('Apply').click()


def fill_in_fields(row, field, value, nap):
    # get reference to element based on lookup of the field
    # NOTE: if field passed as an int, it is referencing one of the days of week
    if isinstance(field, int):
        elem = driver.find_element_by_xpath(get_gte_day_element(field, row))
    else:
        elem = driver.find_element_by_xpath(get_gte_element(field, row))
    # fill in the value
    elem.send_keys(str(value))
    # tab to next field so field takes
    webdriver.ActionChains(driver).send_keys(Keys.TAB).perform()
    # nap time to allow for some XHR to happen
    timer.sleep(nap)


def find_button(name):
    buttons = driver.find_elements_by_css_selector('.x80')
    for button in buttons:
        if button.text == name:
            return button
    return None


def get_gte_comment_element(day_of_week):
    return '//*[@id="B15_{}_N1"]'.format(str(day_of_week))


def get_gte_day_element(day_of_week, row):
    return '//*[@id="B22_{}_{}"]'.format(str(row), str(day_of_week))


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
        "Add Another Row": "/html/body/div[5]/form/span[2]/div[3]/div/div[1]/div/div[3]/div[1]/div[2]/" +
                           "span[1]/span/table[1]/tbody/tr/td/table[2]/tbody/tr[5]/td/table/tbody/tr[6]/" +
                           "td[2]/table/tbody/tr[3]/td[1]/table/tbody/tr/td[1]/button"
    }

    return gte_xpath_map.get(name).format(str(row))


def get_mapped_project_task(key):
    codes = key.split('|')
    project = codes[0].strip()
    task = codes[1].strip() if len(codes) > 1 else ''
    name = '(Name not mapped)'
    project_map = config['gte']['project_map'].get(project, None)
    if project_map:
        project = project_map.get('project', project_map.get('Project Details', project))
        name = project_map.get('name', name)
        force_task = project_map.get('force_task', False)
        if force_task or len(task) == 0:
            task = project_map.get('task', project_map.get('Task Details', task))

    if len(str(task).strip()) == 0:
        raise NameError('Not enough information for project and task lookups')

    return project, task, name


def get_start_end_week(seed_date):
    starter = parse(seed_date)
    start_week = starter - timedelta(days=(starter.weekday()))
    start_week = start_week.replace(hour=0, minute=0, second=0, microsecond=0)
    end_week = start_week + timedelta(days=7) - timedelta(seconds=1)

    return start_week, end_week


def get_timesheet(start, end):
    if config.get('input_method', 'text') == 'clockify':
        entries = get_timesheet_from_clockify(start, end)
    else:
        entries = get_timesheet_from_text()

    return entries


def get_timesheet_from_clockify(start, end):
    use_test_csv = config.get('use_test_csv')

    if use_test_csv:
        stream = open(use_test_csv, mode='r')
    else:
        resp = clockify_api_request(end, start)

        if create_temp_file:
            stream = open('workfile.csv', mode='w+')
            stream.write(resp.text)
            stream.seek(0)
        else:
            stream = io.StringIO(resp.text)

    reader = csv.DictReader(stream)
    entries = []
    for row in reader:
        entries.append(row)
    stream.close()

    return entries


def get_timesheet_from_text():
    with open('time-entries.txt', 'r') as stream:
        lines = stream.readlines()
        entries = []
        this_date = 0
        for line in lines:
            if line.strip() == '':
                continue

            try:
                temp = parse(line)
                this_date = temp
                continue
            except ValueError:
                raw_project, description, raw_minutes = line.split(',')
                minutes = int(raw_minutes)

                project_map = config['gte']['project_map'].get(raw_project)
                if project_map:
                    project = project_map.get('project', project_map.get('Project Details', raw_project))
                    task = project_map.get('task', project_map.get('Task Details'))
                else:
                    raise ValueError('Bad lookup - project: {}'.format(raw_project))

                entry = {
                    "Project": project,
                    "Task": task,
                    "Description": description,
                    "Start Date": this_date.strftime('%m/%d/%Y'),
                    "Duration (decimal)": str(float(minutes / 60)),
                    "Duration (h)": "{:02d}:{:02d}:00".format(int(minutes/60), minutes % 60)
                }
                entries.append(entry)

    return entries


def login():
    driver.get("https://upp.capgemini.com/")
    try:
        elem = WebDriverWait(driver, delay).until(expected_conditions.presence_of_element_located((By.ID, 'login')))
        elem.send_keys(config['gte']['credentials']['user'])
        elem = WebDriverWait(driver, delay).until(expected_conditions.presence_of_element_located((By.ID, 'passwd')))
        elem.click()
        print("IN BROWSER: Please enter your MobilePass code and click 'Log On' button to proceed...")
    except TimeoutException:
        print("Loading took too much time!")

    try:
        single_sign_on_url = expected_conditions.url_contains("sspoam.capgemini.com")
        WebDriverWait(driver, input_delay).until(single_sign_on_url)
    except TimeoutException:
        print("Timed out waiting for SSO url")
        raise NameError("SSO timeout")

    print("Proceeding...")
    # Click on that lame login button on the page with the huge missing image.
    btn = driver.find_element_by_css_selector("body > button:nth-child(2)")
    btn.click()

    try:
        ec = expected_conditions.title_contains("Oracle Access Management")
        WebDriverWait(driver, delay).until(ec)
    except TimeoutException:
        print("Timed out waiting on Oracle login page")
        raise NameError("No oracle login page")

    elem = driver.find_element_by_xpath("//*[@id=\"username\"]")
    elem.send_keys(config['gte']['credentials']['user'])
    elem = driver.find_element_by_xpath("//*[@id=\"password\"]")
    temp_pass = config['gte']['credentials'].get('password', '').strip()
    if len(temp_pass) > 0:
        elem.send_keys(temp_pass)
        elem.send_keys(Keys.RETURN)
    else:
        elem.click()
        print("IN BROWSER: Please enter your Capgemini password and click 'Login' button to proceed...")

    # we don't want to hold password in memory if at all possible
    del temp_pass, config['gte']['credentials']['password']

    try:
        ec = expected_conditions.url_contains("upp.capgemini.com/OA_HTML")
        WebDriverWait(driver, input_delay).until(ec)
    except TimeoutException:
        print("Timed out waiting on GTE main page")
        raise NameError("No GTE main page")

    print("Proceeding...")
    # At the Recent Timecard page, either find the proper timesheet or create a new one
    driver.get("https://upp.capgemini.com/OA_HTML/RF.jsp?function_id=11644")
    find_date = start_of_week.strftime('%d-%b-%Y')
    xpath = "//table[@id='Hxctcarecentlist:Content']//tr[td//text()='Working' and td//text()='{}']".format(find_date)
    elements = driver.find_elements_by_xpath(xpath)
    if len(elements) == 0:
        # must create a new timecard
        create_button = find_button('Create Timecard')
        create_button.click()
        try:
            ec = expected_conditions.presence_of_element_located((By.ID, 'A241N1display'))
            WebDriverWait(driver, delay).until(ec)
            select = Select(driver.find_element_by_id('N75'))
            selected_option = select.first_selected_option
            wanted_range = "{} - {}".format(
                start_of_week.strftime('%B %d, %Y'),
                end_of_week.strftime('%B %d, %Y')
            )
            # Here is where we need to figure out if it's the right timecard?
            if selected_option.text != wanted_range:
                if check_timesheet_date:
                    raise NameError("This is not the expected Timecard")
                else:
                    pass
            else:
                pass
        except TimeoutException:
            print("Timed out waiting on Timecard Create page")
            raise NameError("No GTE Timecard create page")
    else:
        # found the right timecard in the "Working" status for this start date
        elem = elements[0].find_element_by_xpath(".//a[contains(@id, 'Hxctcarecentlist:UpdEnable')]")
        elem.click()


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
test_data_file = config.get('use_test_csv')

if config.get('input_method', 'text') == 'clockify' and not test_data_file:
    # try to figure out user_id and workspace from clockify using API key
    pull_clockify_info()

# Setup dates for report
if config.get("use_week"):
    default_date = config["use_week"]
else:
    start_of_week, end_of_week = get_start_end_week(str(datetime.now().date()))
    print("\n\nClockify to GTE")
    print("-----------------------------------------------------")
    print("Enter any date in the week to use (format YYYY-MM-DD)")
    default_date = input("<ENTER> for default ({}): ".format(str(datetime.now().date()))) or start_of_week.date()

start_of_week, end_of_week = get_start_end_week(str(default_date))
print("Using date {}, report will be from {} to {}".format(default_date, start_of_week, end_of_week))

# get range of entries from input_method
debug_timesheet_entries = get_timesheet(start=start_of_week, end=end_of_week)
# arrange those entries in the most efficient way to enter the data into GTE
reconfigured_timesheets = transform_data(debug_timesheet_entries)

if use_browser == 'Chrome':
    driver = webdriver.Chrome()
elif use_browser == 'Firefox':
    driver = webdriver.Firefox()

driver.set_window_size(1600, 900)

# let's get logged into the application
if gte_debug:
    path = os.getcwd()
    driver.get("file://{}/htestml/index.html".format(path))
else:
    login()

# check to see if timesheet already used/has values
attribute_value = ''
for x in range(0, 7):
    attribute_value += str(driver.find_element_by_xpath('//*[@id="B22_1_{}"]'.format(str(x))).get_attribute('value'))
if len(attribute_value.strip()):
    raise ValueError("Warning!  Detected an already saved timesheet, not proceeding.")

auto_input_data(reconfigured_timesheets)

print("Hours are at: {}".format(sum(totals)))
