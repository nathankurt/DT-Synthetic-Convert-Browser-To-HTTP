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

class InputError(Exception):
    def __init__(self, expression, message):
        self.expression = expression
        self.message = message


#TODO Add filename to logger
logging.basicConfig(format='%(asctime)s %(message)s', level=logging.DEBUG)

parser = argparse.ArgumentParser(description="Convert Browser Monitors to HTTP Monitors")

parser.add_argument("url", help="tenant url with SaaS format: https://[tenant_key].live.dynatrace.com OR Managed: https://{your-domain}/e/{your-environment-id}")

parser.add_argument("token", type=str, help="Your API Token generated with access")

parser.add_argument("-q", "--quiet", help="no output printed to the terminal", action="store_true")

#Lists the management zones in case you don't know the ID's to hit. 
parser.add_argument("-l", "--list", help="list the management zone names and IDs, as well as HTTP location names and IDs", action="store_true")

parser.add_argument("--location", nargs="+", action="append", help="Add locations that you would like to use for ")
#If there are certain tags of monitors that you don't want to transfer over, you can go ahead and set those here in a list
parser.add_argument("--exclude_tags", help="add tags that you want excluded from being transferred over, each tag you want excluded use the arg again", action="append")

parser.add_argument("--include_tag", help="Add tags that you want included to be transferred over as well. If you have a management zone listed, that will take priority and only include things in that management zone. Multiple tags require multiple args added. \
    For Example: --include_tag Retail Advisor --include_tag Retail", action="append")
parser.add_argument("-f", "--frequency", help="sets the frequency of the new monitors, if not listed it will just use the same times they had from before. insert number as integer in minutes. If value isn't available, it will be rounded up to nearest value")




## A mutually exclusive group so you can only ask for keep old or delete old. 
group1 = parser.add_mutually_exclusive_group()

group1.add_argument("-k", "--keep_old", help="doesn't disable the old browser monitors so you have two running concurrently")

group1.add_argument("-d", "--delete", help="Deletes the old browser monitor", action="store_true")

#Can only select some of these
mz_group = parser.add_mutually_exclusive_group()

mz_group.add_argument("-m", "--management_zone", help="Management Zone to select, use the --list feature to get the MZ IDs if you don't know them already.")

mz_group.add_argument("-a", "--all", help="Selects all browser monitors in the environment, USE WITH CAUTION will raise exception if it's not listed", action="store_true")

mz_group.add_argument("-s", "--select_monitor_id", help="Gets a single browser monitor and converts that to an HTTP monitor. Can add multiple Ids by listing with a space inbetween or calling the -s again ", nargs='+', action="append")

##TODO Management zone to exclude

##TODO Sort by tag

# Grab the arguments 
args = parser.parse_args()

# tenant = args.url

# if args.mz
# management_zone = args.m

api_token = args.token

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
        #self.extras = extras
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

            logging.info(f"Request URL: {args['url']}")
              
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
        if args:
            self.endpoint = self.endpoint + "&"
            if args.management_zone:
                self.endpoint = self.endpoint + "managementZone=" + args.management_zone
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
        

class MakeRequest(object):

    def __init__(self,tenant, *args):
        self.tenant = tenant

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


    







##TODO Find maintenence windows things are in and add them to maintenence windows. 
  # First thing to do is create http monitors and get their IDs, store them in dict [browser_val:http_val]
  # Look through all of the apps and windows, grab browser monitors that are in the list store it in a dict
  # Look through all of the 


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



# class ManagementZone:
#     def __init__(self, tenant, mz_id):
#         self.tenant = tenant
#         self.mz_id = mz_id

#     @GetOneRequest(endpoint="api/config/v1/management")
#     def get_management_zone(self):
    

class HttpMonitor(SyntheticMonitor):
    def __init__(self, tenant, http_monitor_id):
        super().__init__(tenant, http_monitor_id)




    
    
class BrowserMonitor(SyntheticMonitor):
    def __init__(self, tenant, b_monitor_id):
        super().__init__(tenant, b_monitor_id)
    

    #Should check the browser monitors and if it fails any threshold, returns false, else returns true
    
    def create_http_json(self,frequency=None):
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
            "rules": []
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
        if frequency:
            json_dict["frequencyMin"] = frequency
        else:
            json_dict["frequencyMin"] = self.b_json["frequencyMin"]


        #transfers problem detection rules over
        json_dict["anomalyDetection"] = self.b_json["anomalyDetection"]


        #checks locations But does not check if location is also available publicly. 
        json_dict["locations"] = self.b_json["locations"]
        #TODO need locations still
        
        #TODO need authetnication still

        #Gets the description and makes it "loading of url"
        for request in json_dict["script"]["requests"]:
            request["description"] = f"Loading of {request['url']}"
        
        for i in range(len(self.b_json["script"]["events"])):
            val = self.b_json["script"]["events"][i]
            if "authentication" in val:
                json_dict["script"]["requests"][i]["authentication"] = {"type": "", "credentials": ""}
                #http monitors use BASIC_AUTHENTICATION while browser monitors just use "basic"
                if val["authentication"]["type"] == "basic":
                    json_dict["script"]["requests"][i]["authentication"]["type"] = "BASIC_AUTHENTICATION"
                
                #if it's something other than webform and basic auth, maybe we'll support it?
                else:
                    json_dict["script"]["requests"][i]["authentication"]["type"] = val["authentication"]["type"]

                #HTTP Uses "credentials: val" instead of "credential {id : val}"
                json_dict["script"]["requests"][i]["authentication"]["credentials"] = val["authentication"]["credential"]["id"]

            
            




        




        return json.dumps(json_dict)

    #should get maintenence windows associated with tag
    def get_maintenence_windows(self):
        pass






        
    #creates new HTTP Monitor From Browser Monitor, Returns ID of New HTTP Monitor
    def create_http(self,args):
        pass
        

#gets a list of http locations with names and entityIds
def get_http_locations(locations):
    dict_list = []
    for location in locations:
        #check if the location can support public http and if it can't, then oops
        if "HTTP" in location["capabilities"] and location["status"] == "ENABLED":
            dict_list.append({"name": location["name"], "entityId": location["entityId"]})
    return dict_list



#create a make request object so can make them more easily
api = MakeRequest(args.url)
    
## List Management Zones and IDs 
if args.list:
    pprint("HTTP Synthetic Monitor Locations: ")
    locations = api.get_location_info().json()
    pprint(get_http_locations(locations))

    pprint("\n\nManagement Zones List: ")
    pprint(api.get_management_zones().json())
    
    
    
#Finish and run the script again without doing anything
    
#Check if single monitor was selected
else:
    browser_monitor_ids = []
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
        logging.error("Input Error: Must Select Filter for monitors, if you want all monitors, make sure to use -a")
        raise InputError("Input Error", "Must select filter for monitors, if all make sure to use -a")
    
    #Empty list so raise exception
    if browser_monitor_ids == []:
        logging.error("Input Error: No Monitors in this scope")
        raise ValueError("No Monitors in this scope")

    
    for b_id in browser_monitor_ids:
        monitor_obj = BrowserMonitor(args.url, b_id)
        # pprint(monitor_obj.b_json)
        b_monitor_type = monitor_obj.b_json["script"]["type"]
        #A browser clickpath monitor which isn't supported
        if b_monitor_type != "availability":
            monitor_obj = ""
            break
        
        #Check if webform authentication, don't transfer because not supported.
        for event in monitor_obj.b_json["script"]["events"]:
            #check if authentication in event, if it is, make sure it's not webform
            if "authentication" in event:
                if event["authentication"]["type"] is "webform":
                    logging.warn("Authentication Type is Webform, Skipping Monitor")
                    break

        #TODO Locations 
        #location does not exist 
        
        pprint(monitor_obj.create_http_json())

        
            
        

## THINGS I DON"T WANT
# Entity ID: 
# Created From
# configuration: Device

        
        


        #TODO Make this new HTTP Monitor
        logging.info(f"Creating Monitor from Old Browser Monitor ID: {b_id} New Browser Monitor ID: {b_id}")





        
        





        
        
        
        




    
    

    


    

    # m_window_ids = api.get_maintenence_windows_ids()

    # #print(m_window_ids)
    # #print(m_window_ids[0])

    # #pprint(look_at_m_windows(args.url))
    # #pprint(MaintenenceWindow(args.url, str(m_window_ids[0])).get_json())
    # pprint(MaintenenceWindow(args.url, str(m_window_ids[0])).__repr__())

#Take Browser Monitor, Convert to HTTP Monitor -> I can probably do that in the class



