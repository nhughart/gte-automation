#Roadmap
pip3 installs needed:
* yaml

Important pieces of information
* per row
    * Project
    * Task
    * Description
    * 'Start Date'
    * 'Duration (decimal)'
    * 'Duration (h)'
    
The way the data is represented IN GTE:
* per row
    * Project
    * Task
        * Global 
            * Type ('RC_Time Std')
            * Site ('Home')
            * Location ('Illinois - No Local - IL - USA')
        * Days 0-6 (Mon, Tue, Wed, Thu, Fri, Sat, Sun)
        * Notes (240 characters per box)
    
What can we do?
API Call to Clockify to get detailed report export in CSV form
Write that file to CSV locally
Ingest input to internal data structure
