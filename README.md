# Convert Dynatrace Browser Monitors to Public HTTP Monitor

This is a program used to convert Dynatrace Synthetic Browser Monitors that are just used for availability monitoring to 

```
usage: convert_browser_to_http.py [-h] [-l] [--convert_disabled]
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