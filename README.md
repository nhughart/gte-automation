# GTE Automation

This program allows the ability to keep a daily log of timesheet entries per day and project code and then automatically upload data to Oracle Time (Known as GTE Time Entry to Capgemini employess)

Usage:
1.  Keep a 'time-entries.txt' file in the format of

```
mm/dd

bucket,description,minutes
```

Example:

```
9/14
internal,did some emails,30
clientA, did some other work,30
clientB, rebuilt the flux capacitor,45

9/15
sick, sick time,120
clientB, did some work,60
```

2.  Map buckets to GTE time fields in time-mapping.json

```
{
    "global": {
        "Type": "RC_Time Std",
        "Site": "Home",
        "Location": "Illinois - No Local - IL - USA",
        "Approver": "All Approvers"
    },
    "cush": {
        "Project Details": "100560527",
        "Task Details": "Overhead"
    },
    "dartta": {
        "Project Details": "100581656",
        "Task Details": "Technical Architecture"
    },
    "dartdesign": {
        "Project Details": "100680067",
        "Task Details": "Technical Architecture"
    }
}
```

3.  Run the program and watch the magic.

```
new day: 9/14
new day: 9/15
new day: 9/16
new day: 9/17
new day: 9/18
[['== 9/14 == day total (480 mins / 8.0 hours) ==',
  'int( 150 mins / 2.5 hours)',
  'sales( 30 mins / 0.5 hours)',
  'cush( 60 mins / 1.0 hours)',
  'dartdesign( 90 mins / 1.5 hours)'],
 ['== 9/15 == day total (480 mins / 8.0 hours) ==',
  'sales( 120 mins / 2.0 hours)',
  'bbwinapp( 30 mins / 0.5 hours)',
  'int( 135 mins / 2.25 hours)'],
 ['== 9/16 == day total (480 mins / 8.0 hours) ==',
  'sales( 45 mins / 0.75 hours)',
  'cush( 30 mins / 0.5 hours)',
  'citta( 180 mins / 3.0 hours)',
  'bbwinapp( 60 mins / 1.0 hours)',
  'int( 75 mins / 1.25 hours)'],
 ['== 9/17 == day total (480 mins / 8.0 hours) ==',
  'clubs( 30 mins / 0.5 hours)',
  'cush( 30 mins / 0.5 hours)',
  'int( 345 mins / 5.75 hours)',
  'bbwinapp( 60 mins / 1.0 hours)'],
 ['== 9/18 == day total (480 mins / 8.0 hours) ==',
  'dartdesign( 270 mins / 4.5 hours)',
  'sales( 120 mins / 2.0 hours)']]

Week total: 2400 mins 40.0 hours
Setting period of timesheet to: september 14

will need 8 rows in gte
        +-- for day: 2020-09-14 00:00:00 (Monday)
                +-- working on bucket for clubs
                +-- working on bucket for int
                +-- working on bucket for sales
                +-- working on bucket for cush
                +-- working on bucket for dartdesign
        +-- for day: 2020-09-15 00:00:00 (Tuesday)
                +-- working on bucket for clubs
                +-- working on bucket for sales
                +-- working on bucket for bbwinapp
                +-- working on bucket for int
        +-- for day: 2020-09-16 00:00:00 (Wednesday)
                +-- working on bucket for clubs
                +-- working on bucket for sales
                +-- working on bucket for cush
                +-- working on bucket for citta
                +-- working on bucket for bbwinapp
                +-- working on bucket for int
        +-- for day: 2020-09-17 00:00:00 (Thursday)
                +-- working on bucket for rap
                +-- working on bucket for clubs
                +-- working on bucket for cush
                +-- working on bucket for int
                +-- working on bucket for bbwinapp
        +-- for day: 2020-09-18 00:00:00 (Friday)
                +-- working on bucket for clubs
                +-- working on bucket for dartdesign
                +-- working on bucket for sales
Filling in task details
Entering detail records for GTE row #0
Entering detail records for GTE row #1
Entering detail records for GTE row #2
Entering detail records for GTE row #3
Entering detail records for GTE row #4
Entering detail records for GTE row #5
Entering detail records for GTE row #6
Entering detail records for GTE row #7
Entering detail records for GTE row #8
```