"""
Created by: Nate Kurt
Last Modified: 7/14/2020

"""


import requests
import json
import argparse
from operator import attrgetter
from pprint import pprint, pformat
import functools
import logging
from itertools import chain
from datetime import datetime



class InputError(Exception):
    def __init__(self, expression, message):
        self.expression = expression
        self.message = message


#logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s', filemode='w', filename="logs/" + datetime.now().strftime('b2http_logfile_%H_%M_%d_%m_%Y.log'), datefmt='%m-%d-%Y %H:%M:%S', level=logging.DEBUG)
logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s', level=logging.DEBUG)


parser = argparse.ArgumentParser(description="Convert Browser Monitors to HTTP Monitors")

parser.add_argument("url", help="tenant url with SaaS format: https://[tenant_key].live.dynatrace.com OR Managed: https://{your-domain}/e/{your-environment-id}")

parser.add_argument("token", type=str, help="Your API Token generated with access")

#TODO Maybe Later, but it outputs it to a file anyways so not a huge deal
#parser.add_argument("-q", "--quiet", help="no output printed to the terminal", action="store_true")

#TODO
#parser.add_argument("--debug", help="prints better logging message", action="store_true")

#Lists the management zones in case you don't know the ID's to hit. 
parser.add_argument("-l", "--list", help="list the management zone names and IDs, as well as HTTP location names and IDs", action="store_true")


parser.add_argument("--convert_disabled", help="also includes values that are disabled", action="store_true")

parser.add_argument("--location", nargs="+", action="append", help="Add locations that you would like to use for ")

parser.add_argument("--overwrite", help="If there is an existing HTTP Monitor with the same name, overwrite it", action="store_true")

#If there are certain tags of monitors that you don't want to transfer over, you can go ahead and set those here in a list
#TODO
parser.add_argument("--exclude-tag", help="add tags that you want excluded from being transferred over, each tag you want excluded use the arg again", action="append")

parser.add_argument("--include_tag", help="Add tags that you want included to be transferred over as well. If you have a management zone listed,\
    that will take priority and only include things in that management zone. Multiple tags require multiple args added. \
    For Example: --include-tag Retail Advisor --include-tag Retail", action="append")

parser.add_argument("-f", "--frequency", help="sets the frequency of the new monitors, if not listed it will just use the same times they had from before.\
     insert number as integer in minutes. values available: 5,10,15,30,60,120,180")




## A mutually exclusive group so you can only ask for keep old or delete old. 
group1 = parser.add_mutually_exclusive_group()

#TODO
group1.add_argument("-k", "--keep_old", help="doesn't disable the old browser monitors so you have two running concurrently", action="store_true")

#TODO
group1.add_argument("--delete", help="Deletes the old browser monitor", action="store_true")

#TODO
group1.add_argument("-d", "--disable", help="Disables old browser monitors but still keeps them there", action="store_true")

#TODO
group1.add_argument("--dry_run", help="Doesn't actually post but does everything else to see if there would be an error", action="store_true")

#Can only select some of these
mz_group = parser.add_mutually_exclusive_group()

mz_group.add_argument("-m", "--management_zone", help="Management Zone to select, use the --list feature to get the MZ IDs if you don't know them already.")

mz_group.add_argument("-a", "--all", help="Selects all browser monitors in the environment, USE WITH CAUTION will raise exception if it's not with any other filters listed", action="store_true")

mz_group.add_argument("-s", "--select_monitor_id", help="Gets a single browser monitor and converts that to an HTTP monitor.\
     Can add multiple Ids by listing with a space inbetween or calling the -s again ", nargs='+', action="append")

##TODO Management zone to exclude

##TODO Sort by tag

# Grab the arguments 
args = parser.parse_args()


# tenant = args.url

# if args.mz
# management_zone = args.m
frequency_ls = [5,10,15,30,60,120,180]

api_token = args.token

#If they select a frequency val, check if input is valid
if args.frequency:

    try:
        val = int(args.frequency)
        assert val in frequency_ls, logging.critical(f"Assertion Error: Frequency must be either {','.join(map(str, frequency_ls))}")

    except TypeError:
        logging.error("Frequency Input must be an integer in minutes.")
    







##Wrapper for requests object, makes things a little bit easier. 
class Request(object):
    def __init__(self, method, endpoint, target=None):
        self.method = method.upper()
        self.h = {
            "Content-Type": "application/json;charset=UTF-8", 
        }
        self.p = {
          "Api-Token": api_token
        }
        self.endpoint = endpoint
        self.target = target


    def __call__(self, f):
    
        def wrapper(obj, *args, **kwargs):
            
            payload = f(obj, *args, **kwargs)


            #Used for when you want to just get one request, set target to extra value you want to add
            """""
            IE: super().__init__("GET", endpoint, target='r_id')
                @GetOneRequest(endpoint="api/config/v1/maintenanceWindows", r_id='self.r_id')  
            """
            url_extras = ""
            if self.target is not None:
                url_extras = getattr(obj,self.target)
        
            
            args = {
              'method': self.method,
              'url': '{}/{}'.format(obj.tenant, self.sanitize_endpoint(self.endpoint + url_extras)),
              'headers': self.h,
              'params': self.p
            }
            if payload is not None:
              args['json'] = payload

            logging.debug(f"Request URL: {args['url']}")
              
            return requests.request(**args)
        return wrapper
    
    def sanitize_endpoint (self, endpoint):
        if endpoint[0] == '/':
            endpoint = endpoint[1:]
        return endpoint


"""
A Subclass of the Request class and used only for get requests, Also lets you add tags and other things if needed. 
"""
class GetRequest(Request):
    def __init__(self, endpoint,args=None):
        #Need to include something for tags and management zone here to create endpoint
        self.endpoint = endpoint
        if args and not args.all:
            if not args.convert_disabled:
                self.endpoint = self.endpoint + "&enabled=true"
            if args.management_zone:
                self.endpoint = self.endpoint + "&managementZone=" + args.management_zone
            if args.include_tag:
                tag_string = "&"
                for x in args.include_tag:
                    tag_string = tag_string + "tag=" + x.replace(" ", "%20") + "&"
                tag_string = tag_string[:-1]

                #["tag=" + x.replace(" ", "%20") + "&" for x in args.include_tag]
                #Removes the last & from the end of the list because it's not needed

                self.endpoint = self.endpoint + tag_string

        super().__init__("GET", self.endpoint)


class GetOneRequest(Request):
    def __init__(self, endpoint,r_id):
        super().__init__("GET", endpoint, target='r_id')
   

class PostRequest(Request):
    def __init__(self, endpoint):
        super().__init__("POST", endpoint)

class PutRequest(Request):
    def __init__(self, endpoint,r_id):
        super().__init__("PUT", endpoint, target='r_id')

class DeleteRequest(Request):
    def __init__(self, endpoint,r_id):
        
        super().__init__("DELETE", endpoint, target='r_id')





#Wrapper function to list the ids when viewing them all. 
def list_ids(func):
    @functools.wraps(func)
    def wrapper_list_ids(*args, **kwargs):
        return ([element['id'] for element in func(*args,**kwargs).json()['values']])
    return wrapper_list_ids

def list_synthetic_ids(func):
    @functools.wraps(func)
    def wrapper_list_ids(*args, **kwargs):
        return ([element['entityId'] for element in func(*args,**kwargs).json()['monitors']])
    return wrapper_list_ids

def list_synthetic_names(func):
    @functools.wraps(func)
    def wrapper_list_names(*args, **kwargs):
        return ([element['name'] for element in func(*args,**kwargs).json()['monitors']])
    return wrapper_list_names

def dict_synthetic_name_id(func):
    @functools.wraps(func)
    def wrapper_list_dict(*args, **kwargs):
        return {element['name']: element['entityId'] for element in func(*args, **kwargs).json()['monitors']}
    return wrapper_list_dict
        

class MakeRequest(object):

    def __init__(self,tenant, r_id="", *args):
        self.tenant = tenant
        self.r_id = r_id

    @GetRequest(endpoint="api/v1/synthetic/monitors?type=BROWSER", args=args)
    def get_browser_monitors(self):
        pass

    @list_synthetic_ids
    def get_browser_monitors_ids(self):
        return self.get_browser_monitors()

    @GetRequest(endpoint="api/config/v1/managementZones")
    def get_management_zones(self):
        pass
        
    @list_ids
    def get_management_zones_ids(self):
        return self.get_management_zones()

    @GetRequest(endpoint="api/config/v1/maintenanceWindows")
    def get_maintenence_windows(self):
        pass

    @list_ids
    def get_maintenence_windows_ids(self):
        return self.get_maintenence_windows()

    @GetRequest(endpoint="api/v1/synthetic/locations")
    def get_location_info(self):
        pass

    @PostRequest(endpoint="api/v1/synthetic/monitors")
    def post_monitor(self, http_json):
        return http_json

    @dict_synthetic_name_id
    @GetRequest(endpoint="api/v1/synthetic/monitors?type=HTTP")
    def get_http_names_id(self):
        pass

    @dict_synthetic_name_id
    @GetRequest(endpoint="api/v1/synthetic/monitors?type=BROWSER",args=args)
    def get_browser_names_id(self):
        pass

    @DeleteRequest(endpoint="api/v1/synthetic/monitors/", r_id = 'r_id')
    def delete_monitor(self):
        pass
        

        

    



    



class MaintenenceWindow:
    def __init__(self,tenant, r_id, *args, **kwargs):
      self.tenant = tenant
      self.r_id = r_id
      self.window_json = self.get_window().json()
    
    @GetOneRequest(endpoint="api/config/v1/maintenanceWindows/", r_id='self.r_id')  
    def get_window(self):
        pass

    def get_new_monitors(self):
        pass

    def update_windows(self):
        pass
        
    def __str__(self):
        return self.get_window().text

    def __repr__(self):
        return pformat(self.get_window().json())


    

class SyntheticMonitor:
    def __init__(self, tenant,r_id):
        self.tenant = tenant
        self.r_id = r_id
        self.b_json = self.get_monitor().json()
        

    
    # def create_new_monitor(self, b_monitor,*args):
    #     MakeRequest(tenant).get_browser_monitors().json()

    @GetOneRequest(endpoint="/api/v1/synthetic/monitors/", r_id='self.r_id')
    def get_monitor(self):
        pass

    def get_tags(self):
        tags_json = [element['key'] for element in self.b_json['tags']]
        return tags_json

    def __str__(self):
        return self.get_monitor().text

    def __repr__(self):
        return pformat(self.get_monitor().json())

    @DeleteRequest(endpoint="/api/v1/synthetic/monitors/", r_id='self.r_id')
    def delete_monitor(self):
        pass

    @PutRequest(endpoint="/api/v1/synthetic/monitors/", r_id='self.r_id')
    def disable_monitor(self):
        self.b_json["enabled"] = False
        return self.b_json
    

class HttpMonitor(SyntheticMonitor):
    def __init__(self, tenant, http_monitor_id):
        super().__init__(tenant, http_monitor_id)




    
    
class BrowserMonitor(SyntheticMonitor):
    def __init__(self, tenant, b_monitor_id):
        super().__init__(tenant, b_monitor_id)
        self.http_json = {}

    #Should check the browser monitors and if it fails any threshold, returns false, else returns true
    
    def create_http_json(self,args,locations):
        json_data = '''{
  "name": "",
  "frequencyMin": 1,
  "enabled": true,
  "type": "HTTP",  
  "script": {
    "version": "1.0",
    "requests": [
      {
        "description": "Loading of Blah Blah Blah",
        "url": "",
        "method": "GET",
        "requestBody": "",
        "validation": {
            "rules": [
                {
                    "value": ">=400",
                    "passIfFound": false,
                    "type": "httpStatusesList"
                }
            ],
            "rulesChaining": "or"
        },
        "configuration": {
          "acceptAnyCertificate": true,
          "followRedirects": true
        },
        "preProcessingScript": "",
        "postProcessingScript": ""
      }
    ]
  },
  "locations": [
  ],
  "anomalyDetection": {
    "outageHandling": {
      "globalOutage": true,
      "localOutage": false,
      "localOutagePolicy": {
        "affectedLocations": 1,
        "consecutiveRuns": 3
      }
    },
    "loadingTimeThresholds": {
      "enabled": false,
      "thresholds": [
        {
          "type": "TOTAL",
          "valueMs": 10000
        }
      ]
    }
  },
  "tags": [],  
  "manuallyAssignedApps": [],
  "automaticallyAssignedApps": []
}'''

        json_dict = json.loads(json_data)

        
        

        
        json_dict["name"] = self.b_json["name"] + " Now HTTP"
        #transfers tags over
        json_dict["tags"] = self.b_json["tags"]
        #transfers apps over
        json_dict["manuallyAssignedApps"] = self.b_json["manuallyAssignedApps"]
        json_dict["automaticallyAssignedApps"] = self.b_json["manuallyAssignedApps"]
        
        
        #If argument set for frequency then use that value, otherwise use the default value of the monitor. 
        if args.frequency:
            json_dict["frequencyMin"] = args.frequency
        else:
            json_dict["frequencyMin"] = self.b_json["frequencyMin"]


        #transfers problem detection rules over
        json_dict["anomalyDetection"] = self.b_json["anomalyDetection"]


        #checks locations But does not check if location is also available publicly. 
        json_dict["locations"] = loc_list
        
        
        
        
        #Checks for authentication per event. 
        for i in range(len(self.b_json["script"]["events"])):
            val = self.b_json["script"]["events"][i]
            json_dict["script"]["requests"][i]["url"] = val["url"]

            if "validate" in val: 
                for j in range(len(val["validate"])):
                    #checks if there are any rules to add other than the fail if greater than 400 error. Not val because they use failiffound vs the other is passiffound. so opposite. 
                    pattern_regex = "regexConstraint" if val["validate"][j]["isRegex"] else "patternConstraint"
                    json_dict["script"]["requests"][i]["validation"]["rules"].append({"value": val["validate"][j]["match"], "passIfFound": not val["validate"][j]["failIfFound"], "type": pattern_regex})
                    #type is pattern match if not regex, else it's regexConstraint

            
            
            if "authentication" in val:
                json_dict["script"]["requests"][i]["authentication"] = {"type": "", "credentials": ""}
                
                #http monitors use BASIC_AUTHENTICATION while browser monitors just use "basic
                if val["authentication"]["type"] == "basic":
                    json_dict["script"]["requests"][i]["authentication"]["type"] = "BASIC_AUTHENTICATION"
                
                #if it's something other than webform and basic auth, maybe we'll support it?
                else:
                    json_dict["script"]["requests"][i]["authentication"]["type"] = val["authentication"]["type"]

                #HTTP Uses "credentials: val" instead of "credential {id : val}"
                json_dict["script"]["requests"][i]["authentication"]["credentials"] = val["authentication"]["credential"]["id"]

        #Gets the description and makes it "loading of url"
        for request in json_dict["script"]["requests"]:
            request["description"] = f"Loading of {request['url']}"
        


        self.http_json = json_dict
        return self.http_json
        #return json.dumps(json_dict)



    
    #creates new HTTP Monitor From Browser Monitor, Returns ID of New HTTP Monitor
    @PostRequest(endpoint="api/v1/synthetic/monitors")
    def create_http(self):
        return self.http_json

    @PutRequest(endpoint="api/v1/synthetic/monitors",r_id='self.r_id')
    def disable_browser(self):
        self.b_json["enabled"] = False
        return self.b_json
        
        

#gets a list of http locations with names and entityIds
def get_http_locations(locations):
    dict_list = []
    for location in locations["locations"]:
        #private location, so no capability there. 
        if location["type"] == "PRIVATE":
            dict_list.append({"name": location["name"], "entityId": location["entityId"]})
        #check if the location can support public http and if it can't, then oops
        elif "HTTP" in location["capabilities"] and location["status"] == "ENABLED":
            dict_list.append({"name": location["name"], "entityId": location["entityId"]})
    return dict_list

#checks the location 
def get_eligible_locations(http_locations, browser_locations,b_id):
    eligible_locations = []
    for location in monitor_obj.b_json["locations"]:
        #check the values of each key "entityId" in the list of dicts http_locations 
        if location in [http["entityId"] for http in http_locations]:
            eligible_locations.append(location)
        else:
            logging.warn(f"Browser Monitor {b_id} using location {location} which either isn't supported yet for HTTP Monitors or Does not exist")
    
    return eligible_locations



#create a make request object so can make them more easily
api = MakeRequest(args.url)
http_locations = get_http_locations(api.get_location_info().json())
## List Management Zones and IDs 
if args.list:
    pprint("HTTP Synthetic Monitor Locations: ")
    
    pprint(http_locations)

    pprint("\n\nManagement Zones List: ")
    pprint(api.get_management_zones().json())
    
    
 
#Finish and run the script again without doing anything
    

else:
    failed_monitors = {}
    #ids to put into after http monitor created that way can reference later. 
    b_monitor_http_monitor_dict = {}
    browser_monitor_ids = []

    #Check if single monitor was selected
    if args.select_monitor_id:
        #Get list of monitors to create and do stuff with
        #flatten list and combine 
        browser_monitor_ids = list(chain.from_iterable(args.select_monitor_id))
    
    elif args.management_zone:
        #TODO Add something to set management zone tag
        # pprint("It's getting here")
        browser_monitor_ids = api.get_browser_monitors_ids()
        
        # monitor = BrowserMonitor(args.url, monitor_ids[0])
        # monitor.get_tags()


    elif not args.all:
        #Raise Exception and say you haven't listed anything.
        logging.critical("Input Error: Must Select Filter for monitors, if you want all monitors, make sure to use -a")
        raise InputError("Input Error", "Must select filter for monitors, if all make sure to use -a")
    else:
        browser_monitor_ids = api.get_browser_monitors_ids()
    #Empty list so raise exception


    browser_names = api.get_browser_names_id()
    http_names = api.get_http_names_id()
    #TODO Get Overwrite Function Working
    if args.overwrite:
        already_made_dict = {} 
        for k in http_names.keys():
            j = k.replace(" Now HTTP", "")
            if j in browser_names.keys():
                already_made_dict.update({browser_names[j]:http_names[k]})



        #pprint(already_made_dict)
    else:
        #Just ignore the ones that have already been made
        already_made_ls = [browser_names[x] for x in browser_names.keys() if x +" Now HTTP" in http_names.keys()]
        if already_made_ls:
            browser_monitor_ids = list(set.difference(set(browser_monitor_ids), set(already_made_ls)))
        

        



    assert browser_monitor_ids != [], logging.critical("Assertion Error, No Monitors in this scope")

    
    for b_id in browser_monitor_ids:
        monitor_obj = BrowserMonitor(args.url, b_id)
        # pprint(monitor_obj.b_json)
        b_monitor_type = monitor_obj.b_json["script"]["type"]
        #A browser clickpath monitor which isn't supported
        if b_monitor_type != "availability":
            logging.warn(f"Browser Clickpath ID: {b_id} Not supported, skipping")
            continue

        #If they wanted excluded tags, checks if they used the args and it worked. 
        if args.exclude_tag: 
            if any(x in monitor_obj.get_tags() for x in args.exclude_tag):
                continue

        
            #Want to overwrite any value with name that already exists 
        
        
        #if they didn't set the location arg, then check if the ones the browser monitor has set by default work fine. 
        if not args.location:
            loc_list = get_eligible_locations(http_locations, monitor_obj.b_json["locations"],b_id)
            if not loc_list:
                logging.critical(f"Browser Monitor {monitor_obj.b_json['name']}(ID: {b_id}) Doesn't have any locations set that are available for public http monitors, you can set a location in the arguments")
                continue
        else:
            loc_list = get_eligible_locations(http_locations, args.location, b_id)
            if not loc_list:
                logging.critical(f"Monitor Locations You Chose are either ineligible or don't exist, check ids that do exist by using the --list command")
                continue
        


        #Check if webform authentication, don't transfer because not supported.
        for event in monitor_obj.b_json["script"]["events"]:
            #check if authentication in event, if it is, make sure it's not webform
            if "authentication" in event:
                if event["authentication"]["type"] == "webform":
                    logging.warn("Authentication Type is Webform, Skipping Monitor")
                    break

    
        
        #pprint(monitor_obj.create_http_json(args, loc_list))
        monitor_obj.create_http_json(args, loc_list)
        

        if not args.dry_run:

            #TODO Check if args.overwrite then delete the old val after we get a 200 response from monitor
            del_id = ""
            if args.overwrite:
                if b_id in already_made_dict.keys():
                    #delete HTTP Monitor
                    del_id = already_made_dict[b_id]


            response = monitor_obj.create_http()
            if response.status_code >= 400:
                logging.error(f"can't post monitor Name: {monitor_obj.b_json['name']}, ID: {b_id}")
                failed_monitors.update({monitor_obj.b_json['name']:b_id})
                continue
            

            #Checks if they want to overwrite, if they don't 
            if args.overwrite and response.status_code < 400:
                del_api = MakeRequest(args.url, r_id=del_id)
                del_response = del_api.delete_monitor()
                #pprint(f"Deletion Status Code: {del_response.status_code}")
                #maybe change the assertion stuff eventually
                assert del_response.status_code < 400, logging.error(f"Unable to delete monitor {del_id}\
                    Error Code: {del_response.status_code}")
                logging.info(f"Overwrote HTTP Monitor: {del_id}")


            
            if args.delete and response.status_code < 400:
                del_b_monitor_response = monitor_obj.delete_monitor()
                assert del_b_monitor_response.status_code < 400, logging.error(f"Unable to delete browser monitor {b_id}\
                    Error Code: {del_b_monitor_response.status_code}")
                logging.info(f"Deleted Old Browser Monitor, Name: {monitor_obj.b_json['name']} ID: {b_id}")
            elif args.disable and response.status_code < 400:
                disable_b_monitor_response = monitor_obj.disable_monitor()
                assert disable_b_monitor_response.status_code < 400, logging.error(f"Unable to disable browser monitor {b_id} \
                    Error Code: {disable_b_monitor_response.status_code}")

            
            assert(response.status_code < 400)
            #pprint(response.json())
            http_id = response.json()["entityId"]
            logging.debug("HTTP ID: " + http_id)
            b_monitor_http_monitor_dict.update({b_id:http_id})

            logging.info(f"Creating Monitor from Old Browser Monitor ID: {b_id} New Browser Monitor ID: {http_id}")

        #empty list so no requirements met. 

        assert b_monitor_http_monitor_dict.keys(), logging.critical("Error: No Monitors in this scope")

        
        
        m_windows = api.get_maintenence_windows_ids()

        for item in m_windows:
            m_window_obj = MaintenenceWindow(args.url, item)
            #for each item in maintenence window look through and if it exists as a key in the list, add the http monitor to the new _json
            for m_id in m_window_obj.window_json["scope"]["entities"]:
                #if it's an all env one, or tag one don't need to bother because it will already be transferred over
                if m_id in b_monitor_http_monitor_dict.keys():
                    m_window_obj.window_json["scope"]["entities"].append(b_monitor_http_monitor_dict[m_id])
                    logging.info(f"Adding HTTP Monitor {b_monitor_http_monitor_dict[m_id]} to Maintenence Window {item}")
                    #Put Request for Window
                    #pprint(m_window_obj.window_json)

    if len(failed_monitors.keys()) > 0:
        pprint("List of failed monitors: ")
        print('\n'.join(['Name: {0:<15} Id: {1}'.format(k,v) for k,v in failed_monitors.items()]))
    else:
        logging.info("All Monitors Successfully Created")




    



