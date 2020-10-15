import csv
import io
import json
import os
from pprint import pprint
import requests

"""
CONFIGURATION
"""
CONFIG_PATH = './config.json'
config = {}
if os.path.isfile(CONFIG_PATH):
    with open(CONFIG_PATH) as config_file:
        config = json.load(config_file)

base_url = 'https://api.clockify.me/api/v1'
report_url = 'https://reports.api.clockify.me/v1'
ext_url = '/workspaces/5f74fd7a337efd7a1619ccd9/reports/detailed'
headers = {"X-Api-Key": "X4SYSEPkQlyHR72Y"}
payload = {
    "dateRangeStart": "2020-10-05T00:00:00Z",
    "dateRangeEnd": "2020-10-11T23:59:59Z",
    "detailedFilter": {
        "page": 1,
        "pageSize": 50,
        "sortColumn": "DATE"
    },
    "exportType": "CSV",
    "users": {
        "ids": ["5f74fd7a337efd7a1619ccd4"],
        "contains": "CONTAINS",
        "status": "ALL"
    }
}


def tester(param):
    if isinstance(param, int):
        print("int")
    elif isinstance(param, str):
        print("str")
    elif isinstance(param, float):
        print("float")
    else:
        print("Not accounted for")


tester(1)
tester(1.5)
tester("1.5")
tester("OPE013")
