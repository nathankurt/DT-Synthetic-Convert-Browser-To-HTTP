import requests
import json
import argparse
from pprint import pprint

parser = argparse.ArgumentParser(description="Convert Browser Monitors to HTTP Monitors")

parser.add_argument("url", help="tenant url with SaaS format: https://[tenant_key].live.dynatrace.com OR Managed: https://***REMOVED***your-domain***REMOVED***/e/***REMOVED***your-environment-id")

parser.add_argument("token", type=str, help="Your API Token generated with access")

parser.add_argument("-q", "--quiet", help="no output printed to the terminal", action="store_true")

#Lists the management zones in case you don't know the ID's to hit. 
parser.add_argument("-l", "--list", help="list the management zone names and IDs", action="store_true")

## A mutually exclusive group so you can only ask for keep old or delete old. 
group1 = parser.add_mutually_exclusive_group()

group1.add_argument("-k", "--keep_old", help="doesn't disable the old browser monitors so you have two running concurrently")

group1.add_argument("-d", "--delete", help="Deletes the old browser monitor", action="store_true")

mz_group = parser.add_mutually_exclusive_group()

mz_group.add_argument("-m", "--management_zone", help="Management Zone to select, use the --list feature to get the MZ IDs if you don't know them already")

mz_group.add_argument("-a", "--all", help="Selects all browser monitors in the environment, USE WITH CAUTION", action="store_true")

mz_group.add_argument("-s", "--single_monitor", help="Gets a single browser monitor and converts that to an HTTP monitor")


# Grab the arguments 
args = parser.parse_args()

tenant = args.url

# if args.mz
# management_zone = args.m

api_token = args.token

auth_headers = ***REMOVED***"Authorization": api_token***REMOVED***


##Wrapper for requests object, makes things a little bit easier. 
class Request(object):
    def __init__(self, method, endpoint):
        self.method = method.upper()
        self.h = ***REMOVED***
            "Content-Type": "application/json;charset=UTF-8", 
***REMOVED***
        self.p = ***REMOVED***
          "Api-Token": api_token
***REMOVED***
        self.endpoint = endpoint

    def __call__(self, f):
      def wrapper(obj, *args, **kwargs):
          payload = f(obj, *args, **kwargs)
          args = ***REMOVED***
              'method': self.method,
              'url': '***REMOVED******REMOVED***/***REMOVED******REMOVED***'.format(obj.tenant, self.sanitize_endpoint(self.endpoint)),
              'headers': self.h,
              'params': self.p
  ***REMOVED***
          if payload is not None:
              args['json'] = payload
          return requests.request(**args)
      return wrapper
    
    def sanitize_endpoint (self, endpoint):
        if endpoint[0] == '/':
            endpoint = endpoint[1:]
        return endpoint



class GetRequest(Request):
    def __init__(self, endpoint):
        super().__init__("GET", endpoint)
    

class PostRequest(Request):
    def __init__(self, endpoint):
        super().__init__("POST", endpoint)

class PutRequest(Request):
    def __init__(self, endpoint):
        super().__init__("PUT", endpoint)

class DeleteRequest(Request):
    def __init__(self, endpoint):
        super().__init__("DELETE", endpoint)



class Endpoint:
    def __init__(self, base, args):
        self.base = base
        self.args = args
        
    
    def get_endpoint(self):
        return self.base

    

        

class MakeRequest(object):
    def __init__(self,tenant):
        self.tenant = tenant
    
    @GetRequest(endpoint=Endpoint("api/v1/synthetic/monitors?type=BROWSER",args).get_endpoint())
    def get_browser_monitors(self):
        pass


    @GetRequest(endpoint="api/config/v1/managementZones")
    def list_management_zones(self):
        pass

    @GetRequest(endpoint="api/config/v1/maintenanceWindows")
    def get_maintenence_windows(self):
        pass

    

    
    



##TODO Find maintenence windows things are in and add them to maintenence windows. 
  # First thing to do is create http monitors and get their IDs, store them in dict [browser_val:http_val]
  # Look through all of the apps and windows, grab browser monitors that are in the list store it in a dict
  # Look through all of the 

class MaintenenceWindow(object):
    def __init__(self,tenant,*args):
      self.tenant = tenant
      self.look_at_windows()

    def look_at_windows(self):
      all_window_ids_json = MakeRequest(tenant).get_maintenence_windows().json()
      all_window_ids_ls = [element['id'] for element in all_window_ids_json['values']]
      return all_window_ids_ls

    def get_new_monitors(self):
        pass

    

class SyntheticMonitor(object):
    def __init__(self, tenant,b_monitor,*args):
        self.tenant = tenant
        self.b_monitor = b_monitor

    
    def create_new_monitor(self, b_monitor,*args):
        MakeRequest(tenant).get_browser_monitors().json()

    def delete_old_monitor(self, b_monitor):
        pass



      
## List Management Zones and IDs 
if args.list:
    api = MakeRequest(args.url)
    print("Maintenance Windows: ")
    pprint(api.list_management_zones().json())

    pprint(api.get_browser_monitors().json())

else:

    pprint(MaintenenceWindow(args.url).look_at_windows())


