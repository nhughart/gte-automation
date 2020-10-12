import csv
from datetime import datetime
from datetime import timedelta
from dateutil.parser import parse
import json
import os
import requests
import tempfile
"""
grab CSV and import that
shove the data into the proper buckets, arrange comments for buckets

NEED:
Clockify API key
Clockify User ID
"""
"""
CONSTANTS
"""
CONFIG_PATH = './config.json'

"""
CONFIGURATION
"""
if os.path.isfile(CONFIG_PATH):
    with open(CONFIG_PATH) as config_file:
        config = json.load(config_file)

"""
GLOBALS
"""

"""
GET CSV FROM CLOCKIFY
"""


def get_start_end_week(seed):
    starter = parse(seed)
    day_of_week = starter.weekday()
    start_week = starter - timedelta(days=day_of_week)
    start_week = start_week.replace(hour=0, minute=0, second=0, microsecond=0)
    end_week = start_week + timedelta(days=7) - timedelta(seconds=1)

    return start_week, end_week

def get_timesheet_from_clockify(start, end):
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
            "ids": ["{}".format(config['clockify']['id']['user'])],
            "contains": "CONTAINS",
            "status": "ALL"
        }
    }
    url = config['clockify']['report']['url'] + config['clockify']['report']['detail_uri'].format(config['clockify']['id']['workspace'])
    headers = {"X-Api-Key": "{}".format(config['clockify']['api']['key'])}

    resp = requests.post(url=url, json=payload, headers=headers)
    entries = []
    with tempfile.NamedTemporaryFile(mode='w+') as temporary_file:
        temporary_file.write(resp.text)
        temporary_file.seek(0)
        reader = csv.DictReader(temporary_file)
        for row in reader:
            entries.append(row)

    return entries


dtnow = datetime.now().date()
start_of_week, end_of_week = get_start_end_week(str(dtnow))

print("Clockify to GTE")
print("---------------")
print("Default week: {}".format(start_of_week.date()))
week = input("Use week (YYYY-MM-DD): ") or start_of_week.date()

start_of_week, end_of_week = get_start_end_week(week)

print(week)
print(start_of_week)
print(end_of_week)


timesheet_entries = get_timesheet_from_clockify(start=start_of_week, end=end_of_week)
exit(0)