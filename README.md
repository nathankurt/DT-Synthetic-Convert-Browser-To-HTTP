# Convert Dynatrace Browser Monitors to Public HTTP Monitor


```
usage: convert_browser_to_http.py [-h] [-q] [-l] [--exclude_tags EXCLUDE_TAGS]
                                  [--include_tag INCLUDE_TAG] [-f FREQUENCY]
                                  [-k KEEP_OLD | -d]
                                  [-m MANAGEMENT_ZONE | -a | -s [SELECT_MONITOR_ID [SELECT_MONITOR_ID ...]]]
                                  url token

Convert Browser Monitors to HTTP Monitors

positional arguments:
  url                   tenant url with SaaS format:
                        https://[tenant_key].live.dynatrace.com OR Managed:
                        https://{your-domain}/e/{your-environment-id
  token                 Your API Token generated with access

optional arguments:
  -h, --help            show this help message and exit
  -q, --quiet           no output printed to the terminal
  -l, --list            list the management zone names and IDs
  --exclude_tags EXCLUDE_TAGS
                        add tags that you want excluded from being transferred
                        over, each tag you want excluded use the arg again
  --include_tag INCLUDE_TAG
                        Add tags that you want included to be transferred over
                        as well. If you have a management zone listed, that
                        will take priority and only include things in that
                        management zone. Multiple tags require multiple args
                        added. For Example: --include_tag Retail Advisor
                        --include_tag Retail
  -f FREQUENCY, --frequency FREQUENCY
                        sets the frequency of the new monitors, if not listed
                        it will just use the same times they had from before.
                        insert number as integer in minutes. If value isn't
                        available, it will be rounded up to nearest value
  -k KEEP_OLD, --keep_old KEEP_OLD
                        doesn't disable the old browser monitors so you have
                        two running concurrently
  -d, --delete          Deletes the old browser monitor
  -m MANAGEMENT_ZONE, --management_zone MANAGEMENT_ZONE
                        Management Zone to select, use the --list feature to
                        get the MZ IDs if you don't know them already.
  -a, --all             Selects all browser monitors in the environment, USE
                        WITH CAUTION will raise exception if it's not listed
  -s [SELECT_MONITOR_ID [SELECT_MONITOR_ID ...]], --select_monitor_id [SELECT_MONITOR_ID [SELECT_MONITOR_ID ...]]
                        Gets a single browser monitor and converts that to an
                        HTTP monitor

```