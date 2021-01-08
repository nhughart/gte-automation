# Clockify to GTE (clock2gte.py)
This program (clock2gte.py) allows users to use a good alternate timekeeping
system: [Clockify](https://clockify.me/) to do the day-to-day time entry.

Then, when it is time to fill out your weekly timesheet, **clock2gte.py** will make use of the Clockify API
to generate a CSV export of the Detailed Report for that week, and use Selenium WebDriver to automate the input
of that data into the Oracle Time (GTE) system.  I forked this from
[Joe Greenwood's original gte-automation](https://github.com/grnwood/gte-automation), and the ability to use a very
simple text file as a means of entering your day to day time entries, if that feels easier.

See INSTALL.md for Python environment requirements!