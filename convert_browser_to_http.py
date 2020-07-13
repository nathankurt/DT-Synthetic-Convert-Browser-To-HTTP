#TODO Get tags and management zones working at the same time. 


import requests
import json
import argparse
from operator import attrgetter
from pprint import pprint
import functools

class InputError(Exception):
    def __init__(self, expression, message):
        self.expression = expression
        self.message = message




parser = argparse.ArgumentParser(description="Convert Browser Monitors to HTTP Monitors")

parser.add_argument("url", help="tenant url with SaaS format: https://[tenant_key].live.dynatrace.com OR Managed: https://***REMOVED***your-domain***REMOVED***/e/***REMOVED***your-environment-id")

parser.add_argument("token", type=str, help="Your API Token generated with access")

parser.add_argument("-q", "--quiet", help="no output printed to the terminal", action="store_true")

#Lists the management zones in case you don't know the ID's to hit. 
parser.add_argument("-l", "--list", help="list the management zone names and IDs", action="store_true")

#If there are certain tags of monitors that you don't want to transfer over, you can go ahead and set those here in a list
parser.add_argument("--exclude_tags", help="add tags that you want excluded to be transferred in a list seperated by spaces", nargs='*')

parser.add_argument("--include_tags", help="Add tags that you want included to be transferred over as well. If you have a management zone listed, that will take priority and only include things in that management zone with that tag")
parser.add_argument("-f", "--frequency", help="sets the frequency of the new monitors, if not listed it will just use the same times they had from before. insert number as integer in minutes. If value isn't available, it will be rounded up to nearest value")




## A mutually exclusive group so you can only ask for keep old or delete old. 
group1 = parser.add_mutually_exclusive_group()

group1.add_argument("-k", "--keep_old", help="doesn't disable the old browser monitors so you have two running concurrently")

group1.add_argument("-d", "--delete", help="Deletes the old browser monitor", action="store_true")

#Can only select some of these
mz_group = parser.add_mutually_exclusive_group()

mz_group.add_argument("-m", "--management_zone", help="Management Zone to select, use the --list feature to get the MZ IDs if you don't know them already.")

mz_group.add_argument("-a", "--all", help="Selects all browser monitors in the environment, USE WITH CAUTION will raise exception if it's not listed", action="store_true")

mz_group.add_argument("-s", "--select_monitor_id", help="Gets a single browser monitor and converts that to an HTTP monitor", nargs='*')

##TODO Management zone to exclude

##TODO Sort by tag

# Grab the arguments 
args = parser.parse_args()

tenant = args.url

# if args.mz
# management_zone = args.m

api_token = args.token

##Wrapper for requests object, makes things a little bit easier. 
class Request(object):
    def __init__(self, method, endpoint, target=None):
        self.method = method.upper()
        self.h = ***REMOVED***
            "Content-Type": "application/json;charset=UTF-8", 
***REMOVED***
        self.p = ***REMOVED***
          "Api-Token": api_token
***REMOVED***
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
        
            
            args = ***REMOVED***
              'method': self.method,
              'url': '***REMOVED******REMOVED***/***REMOVED******REMOVED***'.format(obj.tenant, self.sanitize_endpoint(self.endpoint + url_extras)),
              'headers': self.h,
              'params': self.p
    ***REMOVED***
            if payload is not None:
              args['json'] = payload

            print(args['url'])
              
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
            if args.include_tags:
                tag_string = ["tag=" + x + "&" for x in args.include_tags]
                #Removes the last & from the end of the list because it's not needed
                tag_string = tag_string[:-1]
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







##TODO Find maintenence windows things are in and add them to maintenence windows. 
  # First thing to do is create http monitors and get their IDs, store them in dict [browser_val:http_val]
  # Look through all of the apps and windows, grab browser monitors that are in the list store it in a dict
  # Look through all of the 


class MaintenenceWindow:
    def __init__(self,tenant, r_id, *args, **kwargs):
      self.tenant = tenant
      self.r_id = r_id
    
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
        return self.get_window().json()

    

class SyntheticMonitor:
    def __init__(self, tenant,r_id):
        self.tenant = tenant
        self.r_id = r_id

    
    # def create_new_monitor(self, b_monitor,*args):
    #     MakeRequest(tenant).get_browser_monitors().json()

    @GetOneRequest(endpoint="/api/v1/synthetic/monitors/", r_id='self.r_id')
    def get_monitor(self):
        pass

    def get_tags(self):
        tags_json = [element['key'] for element in self.__repr__()['tags']]
        print(tags_json)

    def __str__(self):
        return self.get_monitor().text

    def __repr__(self):
        return self.get_monitor().json()


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
    def __check_eligibility(self,args):
        if args.exclude_tags:
            #If Monitor contains tag that is in the excluded list, remove from list
            pass
        pass

    #should get maintenence windows associated with tag
    def get_maintenence_windows(self):
        pass

        
    #creates new HTTP Monitor From Browser Monitor, Returns ID of New HTTP Monitor
    def create_http(self,args):
        if self.__check_eligibility(args):
            #Do Stuff
            pass
        else:
            return None



api = MakeRequest(args.url)
    
## List Management Zones and IDs 
if args.list:

    pprint(api.get_management_zones().json())
    #pprint(api.get_management_zones_ids())
    
#Finish and run the script again without doing anything
    
#Check if single monitor was selected
else:
    monitor_ids = []
    if args.select_monitor_id:
        #Get list of monitors to create and do stuff with
        monitor_ids = args.select_monitor_id 
    
    elif args.management_zone:
        #TODO Add something to set management zone tag
        # pprint("It's getting here")
        monitor_ids = api.get_browser_monitors_ids()
        
        # monitor = BrowserMonitor(args.url, monitor_ids[0])
        # monitor.get_tags()


    elif not args.all:
        #Raise Exception and say you haven't listed anything.
        raise InputError("Input Error", "Must select filter for monitors, if all make sure to use -a")
    
    if monitor_ids == []:
        raise ValueError("No Monitors in this scope")
    


    

    # m_window_ids = api.get_maintenence_windows_ids()

    # #print(m_window_ids)
    # #print(m_window_ids[0])

    # #pprint(look_at_m_windows(args.url))
    # #pprint(MaintenenceWindow(args.url, str(m_window_ids[0])).get_json())
    # pprint(MaintenenceWindow(args.url, str(m_window_ids[0])).__repr__())

#Take Browser Monitor, Convert to HTTP Monitor -> I can probably do that in the class



