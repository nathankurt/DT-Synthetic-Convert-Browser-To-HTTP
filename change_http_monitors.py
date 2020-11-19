import requests
import json
import argparse
from operator import attrgetter
from pprint import pprint, pformat
import functools
import logging
from itertools import chain
from datetime import datetime
from sys import stdout



class InputError(Exception):
    def __init__(self, expression, message):
        self.expression = expression
        self.message = message




logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s', filemode='a', filename="logs/" + datetime.now().strftime('b2http_logfile_%H_%M_%d_%m_%Y.log'), datefmt='%m-%d-%Y %H:%M:%S', level=logging.DEBUG)
#logging.basicConfig(datefmt='%m-%d-%Y %H:%M:%S')

#logging.basicConfig(level=logging.INFO, filemode='w')


parser = argparse.ArgumentParser(description="Convert Browser Monitors to HTTP Monitors")

parser.add_argument("url", help="tenant url with SaaS format: https://[tenant_key].live.dynatrace.com OR Managed: https://{your-domain}/e/{your-environment-id}")

parser.add_argument("token", type=str, help="Your API Token generated with access")

debug_level_group = parser.add_mutually_exclusive_group()

debug_level_group.add_argument("-q", "--quiet", help="no output printed to the terminal", action="store_true")

debug_level_group.add_argument("--debug", help="prints better logging message", action="store_true")

#Lists the management zones in case you don't know the ID's to hit. 
parser.add_argument("-l", "--list", help="list the management zone names and IDs, as well as HTTP location names and IDs", action="store_true")

parser.add_argument("--timeout", help="Sets the HTTP Monitor Request Timeout")
parser.add_argument("--convert_disabled", help="also includes values that are disabled", action="store_true")

parser.add_argument("--location", nargs="+", action="append", help="Add locations that you would like to use for ")

parser.add_argument("--overwrite", help="If there is an existing HTTP Monitor with the same name, overwrite it", action="store_true")

#If there are certain tags of monitors that you don't want to transfer over, you can go ahead and set those here in a list

parser.add_argument("--exclude-tag", help="add tags that you want excluded from being transferred over, each tag you want excluded use the arg again", action="append")

parser.add_argument("--include_tag", help="Add tags that you want included to be transferred over as well. If you have a management zone listed,\
    that will take priority and only include things in that management zone. Multiple tags require multiple args added. \
    For Example: --include-tag Retail Advisor --include-tag Retail", action="append")

parser.add_argument("-f", "--frequency", help="sets the frequency of the new monitors, if not listed it will just use the same times they had from before.\
     insert number as integer in minutes. values available: 5,10,15,30,60,120,180")



## A mutually exclusive group so you can only ask for keep old or delete old. 
group1 = parser.add_mutually_exclusive_group()


group1.add_argument("-k", "--keep_old", help="doesn't disable the old browser monitors so you have two running concurrently", action="store_true")


group1.add_argument("--delete", help="Deletes the old browser monitor", action="store_true")


group1.add_argument("-d", "--disable", help="Disables old browser monitors but still keeps them there", action="store_true")


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



logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


c_handler = logging.StreamHandler(stream=stdout)
f_name = "logs/" + datetime.now().strftime('b2http_logfile_%H_%M_%m-%d-%Y.log')
f_handler = logging.FileHandler(f_name, mode='w')



f_format = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt='%m-%d-%Y %H:%M:%S')

c_format = logging.Formatter("[%(levelname)s] %(message)s")
c_handler.setFormatter(c_format)
f_handler.setFormatter(f_format)

f_handler.setLevel(logging.DEBUG)
logger.addHandler(f_handler)

if args.debug:
    logger.setLevel(logging.DEBUG)
    c_handler.setLevel(logging.DEBUG)
    logger.addHandler(c_handler)
elif not args.quiet:
    c_handler.setLevel(logging.INFO)
    logger.addHandler(c_handler)



# logger.debug("debug message")
# logger.info("info message")
# logger.warning("warn message")
# logger.error("error message")
# logger.critical("critical message")

#Santizie Endpoint
#Change http to https if there
args.url = args.url.replace("http://", "https://")
# logger.debug("HTTP in url detected, using https instead")
try:
    args.url = args.url.rstrip("/ ")
except: 
    logger.error(f"URL: {args.url} Malformed")



# tenant = args.url

#frequency list that contains possible values for frequencies you can have. 
frequency_ls = [5,10,15,30,60,120,180]

api_token = args.token

#If they select a frequency val, check if input is valid
if args.frequency:

    try:
        val = int(args.frequency)
        assert val in frequency_ls, logger.critical(f"Assertion Error: Frequency must be either {','.join(map(str, frequency_ls))}")

    except TypeError:
        logger.error("Frequency Input must be an integer in minutes.")

    

if args.timeout:
    try:
        val = int(args.timeout)
        assert val > 0 and val <= 60, logger.critical(f"Assertion Error: Timeout must be integer between 1 and 60")

    except TypeError:
        logger.error("Timeout must be an integer between 1 and 60")





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

            logger.debug(f"{self.method} Request URL: {args['url']}")
              
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

def list_http_ids(func):
    @functools.wraps(func)
    def wrapper_list_ids(*args, **kwargs):
        return ([element['entityId'] for element in func(*args, **kwargs).json()['monitors'] if element['type'] == "HTTP"])
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
        
#The class you call for making a certain request- uses the request wrapper
class MakeRequest(object):

    def __init__(self,tenant, r_id="", *args):
        self.tenant = tenant
        self.r_id = r_id

    @GetRequest(endpoint="api/v1/synthetic/monitors", args=args)
    def get_monitors(self):
        pass

    @GetRequest(endpoint="api/v1/synthetic/monitors?type=HTTP", args=args)
    def get_http_monitors(self):
        pass


    #Get request for all browser monitors
    @GetRequest(endpoint="api/v1/synthetic/monitors?type=BROWSER", args=args)
    def get_browser_monitors(self):
        pass

    #Get All of the browser_monitor Ids
    @list_synthetic_ids
    def get_browser_monitors_ids(self):
        return self.get_browser_monitors()

    @list_synthetic_ids
    def get_http_monitors_ids(self):
        return self.get_http_monitors()

    #Get management zones names and IDs
    @GetRequest(endpoint="api/config/v1/managementZones")
    def get_management_zones(self):
        pass
        
    #get just list of management zones IDS
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

    @PutRequest(endpoint="api/config/v1/maintenanceWindows/", r_id='self.r_id')
    def update_window(self, monitor_id):
        self.window_json["scope"]["entities"].append(monitor_id)
        return self.window_json

    def __str__(self):
        return self.get_window().text

    def __repr__(self):
        return pformat(self.get_window().json())


    

class SyntheticMonitor:
    def __init__(self, tenant,r_id):
        self.tenant = tenant
        self.r_id = r_id
        self.b_json = self.get_monitor().json()
        self.b_name = self.get_monitor().json()["name"]
        

    
    # def create_new_monitor(self, b_monitor,*args):
    #     MakeRequest(tenant).get_browser_monitors().json()

    @GetOneRequest(endpoint="/api/v1/synthetic/monitors/", r_id='self.r_id')
    def get_monitor(self):
        pass

    def get_tags(self):
        tags_json = [element['key'] for element in self.b_json['tags']]
        return tags_json


    @DeleteRequest(endpoint="/api/v1/synthetic/monitors/", r_id='self.r_id')
    def delete_monitor(self):
        pass

    @PutRequest(endpoint="/api/v1/synthetic/monitors/", r_id='self.r_id')
    def disable_monitor(self):
        self.b_json["enabled"] = False
        return self.b_json

    

    
    def __str__(self):
        return self.get_monitor().text

    def __repr__(self):
        return pformat(self.get_monitor().json())
    

class HttpMonitor(SyntheticMonitor):
    def __init__(self, tenant, http_monitor_id):
        super().__init__(tenant, http_monitor_id)

    

    @PutRequest(endpoint="/api/v1/synthetic/monitors/", r_id='self.r_id')
    def update_timeout(self, timeout_val):
        ls_requests = self.b_json["script"]["requests"]
        for req in ls_requests:
            req["requestTimeout"] = timeout_val
        
        self.b_json["script"]["requests"] = ls_requests
        return self.b_json


api = MakeRequest(args.url)

failed_monitors = {}

http_monitor_id = api.get_http_monitors_ids()
if not args.timeout:
    args.timeout = 60

for http_id in http_monitor_id:
    http_monitor = HttpMonitor(args.url, http_id)
    timeout_response = http_monitor.update_timeout(args.timeout)
    assert timeout_response.status_code < 400, logger.error(f"Unable to update monitor {http_id}\
        Error Code: {timeout_response.status_code}")
    logger.info(f"Updated Timeout for {http_monitor.b_name} - {http_id}")







