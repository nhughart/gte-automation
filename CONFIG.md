# CONFIG.md
## Configuration
### Types
1. YML (Yaml)
    * Name of the file: config.yml
    * An example is given, named: config.sample.yml
2. JSON
    * Name of the file: config.json
    * An example is given, named: config.sample.json
#### Taxonomy
* **input_method** - SETTING: This determines if we will interface with Clockify or a named text file (or some
  future API to get a week's worth of timesheet data)
    * **clockify** - this value will query Clockify's report API in order to grab a week of data in the form of the
      detailed report.  To use this option, you will also need to provide the API key (more information in
      the *clockify* section below
    * **text** - this fill interpret a file such as demonstrated by the "time-entries.txt.sample" file.  Where entries
      are required to be grouped under the date.  Each line should have 3 fields, separated by commas:
      * **project alias** - this alias will be the key in the GTE Project Map (more information in
        the **gte** section below)
      * **description** - this should be a brief description of the work performed, it should NOT contain any commas,
        as that will confuse the simple parsing algorithm
      * **minutes_spent** - the number of minutes spent - the system will translate this time into decimal hours  
* **use_browser** - SETTING: This is the Selenium browser choice.  Both Firefox and Chrome work well.
    * **Firefox** - use the Selenium Firefox driver (must have Firefox already installed on your system)
    * **Chrome** - use the Selenium Chrome driver (must have Chrome already installed on your system)
* **use_test_csv** - SETTING: only used during testing to circumvent the Clockify calls, so I can provide the
  system data that might not be easy to replicate in Clockify.  If provided, it should be the name of an existing
  CSV file in the format of the Clockify Detailed Report CSV export (as would be created by setting
  the **create_temp_file** setting in the "clockify" section).
* **use_week** - SETTING: By entering a date value here, it bypasses the normal input/entry of date to
  use (which would default to today, and then figure out the start/end dates for API and data entry purposes)
    * **YYYY-MM-DD** - probably needs quotes to work (JSON = double quotes)
    * **null/empty** - the simplest way to null this out is to remove the key from the file
        * **YML** - (use_week:)
        * **JSON** - ("use_week": null)
* **clockify** - SECTION: if you chose the **input_method** of "clockify", this section will need to be filled out
  in order to properly communicate with the Clockify API to get the Detailed Report.  It is important to know
  * **create_temp_file** - SETTING: Determines if we create a file when we ask Clockify to export the CSV of the
    Detailed Report.  It can be useful for debugging purposes to see the actual data returned from the report.
    * **VALUES**
      * 0 - Means don't bother with intermediary file.  You can also remove the key altogether an it defaults to 0
      * 1 - Means create the file, it will be called "workfile.csv"
  * **api** - SECTION: this holds 2 keys
    * **key** - SETTING: The API key.  You get a key from Clockify by going to Settings, Profile, then in the API
      section you look in the API Key area.  If there isn't one already, you might need to click the Generate button
    * **url** - SETTING: This should be: https://api.clockify.me/api/v1, it's not really a setting, but it's here
      in case it changes in the future, as well as to be a reference for additional API implementations
  * **report** - SECTION: This section is pretty static also.  These are here in case it changes in the future,
    as well as to be a reference for additional API implementations
    * **detail_uri** - SETTING: Should be "/workspaces/{}/reports/detailed".  The {} is there to hold
      the workspace_id that we get from the default_workspace field during an initial API call (where we also
      get the user_id of the owner of the API key so we can generate the report for ONLY that user)
    * **url** - SETTING: The URL for the reports is slightly different than the normal API URL, it should be:
    https://reports.api.clockify.me/v1, na is provided as a setting in case it changes in the future,
    as well as to be a reference for additional API implementations
* **gte** - SECTION: Holds GTE related information
    * **settings** - SECTION: mostly debugging settings
        * **debug** - this should be left 0
    * **credentials** - SECTION: Holds username (and optional password) for assisting in logging in
        * **user** - SETTING: this username should be the 7+1 username.  It will prefill in 2 places:
            * the MobilePass SSO page (where you will still need to enter your 6-digit MobilePass generated password)
            * the Capgemini user/pass screen that for some reason happens after the SSO page
        * **password** - SETTING: ```USE THIS SETTING AT YOUR OWN RISK!!!```  This is only provided as an
          extreme lazy option where it will fill-in your password in the Capgemini user/pass screen.  **USE THIS
          AT YOUR OWN RISK**  It is not advised to record your password in clear text EVER _EVER_!
    * **global** - SECTION: We are now down to the mapping of values that will be entered into the timesheet.  You
      should manually find these values from either past timesheets.  You should copy/paste these values carefully
      from GTE, as they need to be exact.
      * **location** - In my case it is: **Illinois - No Local - IL - USA**
      * **site** - For most people this is and will continue to be: **Home**
      * **type** - If you are salaried, it will always be: **RC_Time Std**
    * **project_map** - SECTION: Here is where we do some mapping (mostly related to the **input_method**=text) of
      projects and tasks.
      * **Project/Task Alias** - In the text input file, you can have a project/task alias of say "asiTL" which
      means something to you, perhaps "Asics TL work".  You might also have "asiD" for "Asics Development work" and
      maybe "asiNBT" for "Asics NBT work".  These type of entries in the map should have the following:
        * **ALIAS** - this key would be **asiTL** or **asiD** or **asiNBT** from the examples listed above.
            * **name** - OPTIONAL - This is not referenced in the program, and is there for your reference to
              identify the map entry
            * **project** - This will be the Project Code we use in our time entry.
            * **Project Details** - Same as **project**.  Provided for compatibility with the time-mapping.json used
              in [Joe Greenwood's original gte-automation](https://github.com/grnwood/gte-automation)
            * **task** - The task associated with the alias, i.e. **NBT**, **Technical Lead**, **Systems
              Administration**, etc.
            * **Task Details** - Same as **task**.  Provided for compatibility with the time-mapping.json used
              in [Joe Greenwood's original gte-automation](https://github.com/grnwood/gte-automation)
      * **Project - fallback task** - For a convenience, I provide the same mapping capability for
        the **input_method**=clockify.  While, with Clockify, you can have multiple tasks with each project you define,
        it is an extra step with each entry to choose not only the project, but also the task.  So, if there is only
        ever one task, or you MOSTLY use one task in a project, you can make a mapping to that fallback task, and skip
        choosing the task during the Clockify entry.  For example, US0799VAC has only one task, an it is "1".  NOTE:
        if you provide a task in the entry in Clockify, it will be used.  This "fallback" task is only used if one is
        not provided in the time entry.
        * **PROJECT** - this key would be the project code, i.e. US0799VAC in the example above
            * **name** - OPTIONAL - This is not referenced in the program, and is there for your reference to
              identify the map entry
            * **task** - The fallback task for the **PROJECT**.  In the example above, it is **1**