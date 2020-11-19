# Convert Dynatrace Browser Monitors to Public HTTP Monitor

This is a program used to convert Dynatrace Synthetic Browser Monitors that are just used for availability monitoring and the only thing stopping them from using HTTP Monitors at the time was that there weren't any public location http monitors at the time. 

That has all changed as of June 2020 for Dynatrace SaaS customers. Now you can use public locations but there isn't an easy way to convert over your browser monitors that were just being used at the time for that purpose as well as transfer things associated with the browser monitor like Maintenence windows etc.

## Use Cases 

* Convert all "blank page" monitors that are really just used for SLAs while changing frequency to make them all more frequent. 

* Open the budget for other things DEM by making pages that aren't fully utilizing browser monitor capabilities into HTTP monitors

## Prerequisites 

* Python Version >= 3.6
* Requests Module (Found in `requirements.txt` and `Pipfile`)
* Dynatrace API Token with the Following Access Turned On:
  * `Create and read synthetic monitors, locations, and nodes`
  * `Read configuration`
  * `Write Configuration`
  * `Read Credential Vault entries`

### Optional 

* Pipenv - Used for Pipfile and virtual environments. 

## Usage for Converting Timeout 

* You can run this program by running `python change_http_monitors.py [url] [api-token] --[options]`

* Download requests module with `pip install -r requirements.txt` after going into a virtual environment(or not I'm not your boss)

positional arguments:
  url                   tenant url with SaaS format:
                        https://[tenant_key].live.dynatrace.com OR Managed:
                        https://{your-domain}/e/{your-environment-id}
  token                 Your API Token generated with access

optional arguments:
  -h, --help            show this help message and exit
  -q, --quiet           no output printed to the terminal
  --debug               prints better logging message
  -l, --list            list the management zone names and IDs, as well as
                        HTTP location names and IDs
  --timeout TIMEOUT     Sets the HTTP Monitor Request Timeout between 0 and 60
  --convert_disabled    also includes values that are disabled
  
  --exclude-tag EXCLUDE_TAG
                        add tags that you want excluded from being transferred
                        over, each tag you want excluded use the arg again
  --include_tag INCLUDE_TAG
                        Add tags that you want included to be transferred over
                        as well. If you have a management zone listed, that
                        will take priority and only include things in that
                        management zone. Multiple tags require multiple args
                        added. For Example: --include-tag Retail Advisor
                        --include-tag Retail

  -m MANAGEMENT_ZONE, --management_zone MANAGEMENT_ZONE
                        Management Zone to select, use the --list feature to
                        get the MZ IDs if you don't know them already.
  -s SELECT_MONITOR_ID [SELECT_MONITOR_ID ...], --select_monitor_id SELECT_MONITOR_ID [SELECT_MONITOR_ID ...]
                        Gets a single browser monitor and converts that to an
                        HTTP monitor. Can add multiple Ids by listing with a
                        space inbetween or calling the -s again


## Usage for HTTP to Browser

* Download requests module with `pip install -r requirements.txt` after going into a virtual environment(or not I'm not your boss)

* You can run this program by running `python convert_browser_to_http.py [url] [api-token] --[options]`

* More details on specifics found below. 


```
usage: convert_browser_to_http.py [-h] [-q | --debug] [-l]
                                  [--convert_disabled]
                                  [--location LOCATION [LOCATION ...]]
                                  [--overwrite] [--exclude-tag EXCLUDE_TAG]
                                  [--include_tag INCLUDE_TAG] [-f FREQUENCY]
                                  [-k | --delete | -d | --dry_run]
                                  [-m MANAGEMENT_ZONE | -a | -s SELECT_MONITOR_ID [SELECT_MONITOR_ID ...]]
                                  url token

Convert Browser Monitors to HTTP Monitors

positional arguments:
  url                   tenant url with SaaS format:
                        https://[tenant_key].live.dynatrace.com OR Managed:
                        https://{your-domain}/e/{your-environment-id}
  token                 Your API Token generated with access

optional arguments:
  -h, --help            show this help message and exit
  -q, --quiet           no output printed to the terminal
  --debug               prints better logging message
  -l, --list            list the management zone names and IDs, as well as
                        HTTP location names and IDs
  --convert_disabled    also includes values that are disabled
  --location LOCATION [LOCATION ...]
                        Add locations that you would like to use for
  --overwrite           If there is an existing HTTP Monitor with the same
                        name, overwrite it
  --exclude-tag EXCLUDE_TAG
                        add tags that you want excluded from being transferred
                        over, each tag you want excluded use the arg again
  --include_tag INCLUDE_TAG
                        Add tags that you want included to be transferred over
                        as well. If you have a management zone listed, that
                        will take priority and only include things in that
                        management zone. Multiple tags require multiple args
                        added. For Example: --include-tag Retail Advisor
                        --include-tag Retail
  -f FREQUENCY, --frequency FREQUENCY
                        sets the frequency of the new monitors, if not listed
                        it will just use the same times they had from before.
                        insert number as integer in minutes. values available:
                        5,10,15,30,60,120,180
  -k, --keep_old        doesn't disable the old browser monitors so you have
                        two running concurrently
  --delete              Deletes the old browser monitor
  -d, --disable         Disables old browser monitors but still keeps them
                        there
  --dry_run             Doesn't actually post but does everything else to see
                        if there would be an error
  -m MANAGEMENT_ZONE, --management_zone MANAGEMENT_ZONE
                        Management Zone to select, use the --list feature to
                        get the MZ IDs if you don't know them already.
  -a, --all             Selects all browser monitors in the environment, USE
                        WITH CAUTION will raise exception if it's not with any
                        other filters listed
  -s SELECT_MONITOR_ID [SELECT_MONITOR_ID ...], --select_monitor_id SELECT_MONITOR_ID [SELECT_MONITOR_ID ...]
                        Gets a single browser monitor and converts that to an
                        HTTP monitor. Can add multiple Ids by listing with a
                        space inbetween or calling the -s again



```

### Examples

