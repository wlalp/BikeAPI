'''Contains the SearchQuery class, and asks the user to watch a demo
 or complete an interactive demo.
 Author: William Pugh'''
import os
import json
import sys
from pathlib import PurePath
import requests

class SearchQuery():
    '''Query object for making GET requests to the bikeindex.org API'''
    def __init__(self,params=None):
        '''Constructor for SearchQuery class. Accepts a dictionary of parameters'''
        self.params = params
        self.url = self.url_builder(self.params)
        self.status = None
        self.results = None
        self.json = None

    def __str__(self):
        '''Returns a string of the query's results'''
        return str(self.results)

    def url_builder(self,params):
        '''Takes a dict of parameters and builds a url to query'''
        base_url = "https://bikeindex.org/api/v3/search?"
        if params is None:
            return base_url
        for par,val in params.items():
            if val is not None and val != "":
                base_url += f"{par}={val}&"
        new = base_url.removesuffix("&")
        return new

    def get_status(self):
        '''Returns the status code of the search's request'''
        stat = requests.head(self.url,timeout=5.0)
        self.status = stat.status_code
    def reset_url(self):
        '''Setter for the URL'''
        self.url = self.url_builder(self.params)

    def get(self):
        '''Performs a GET request using the object's url
          and returns a JSON dictionary if successful'''
        self.reset_url()
        self.get_status()
        if self.status != 200 or self.is_empty():
            print("The given URL is not available")
            return None
        print("Getting query information...")
        req = requests.get(self.url,timeout=5.0)
        j = req.json()
        self.set_results(j)
        print(f"{len(self.results)} results received...")
        self.json = j
        return j

    def set_results(self,result):
        '''Setter method for results'''
        self.results = list(result["bikes"])

    def save_images(self,dir_name= None):
        '''Saves the images to a subdirectory,
          if no name is given a name will be automatically generated'''
        images = []
        if dir_name is None:
            dir_name = self._subdir_name()

        for res in self.results:
            image = {"title":None,"url":None}
            if res["large_img"] is not None:
                image["title"], image["url"] = res["title"] ,res["large_img"]
                images.append(image)

        if len(images) < 1:
            print("No images found.")
            return None
        _dir = self._subdir(dir_name)
        if _dir is None:
            return None
        print(f"Recieved {len(images)} images.\nWriting to {_dir}...\n")
        for i in images:
            i_filetype = i["url"].split('.')[-1]
            filename = f'{i["title"]}.{i_filetype}'
            img_path = _dir / filename
            with open(img_path, 'wb') as file:
                file.write(requests.get(i["url"],timeout=5.0).content)
            print(f"{filename:<40} written successfuly!")
        return images

    def _subdir(self,name):
        '''Creates a subdirectory in the current working directory'''
        if name is None:
            return None
        _dir = PurePath(__file__)
        _dir = _dir.parent
        _dir = _dir / name
        if not os.path.exists(_dir):
            os.mkdir(_dir)
        return _dir

    def _subdir_name(self):
        '''Helper method that builds the name of a file from the parameters of the search'''
        name = ""
        if self.is_empty():
            return None
        for par, val in self.params.items():
            if val is None:
                continue
            name += f"{par}={val}_"

        name = name.removesuffix("_")
        if name.endswith("& C"):
            name = name.removesuffix("& C")
        return name

    def split_params(self,p_string):
        '''Returns a dictionary of the parameters in the given input string.
          Conforms to "key=value-key=value-key=value" syntax'''
        if p_string is None:
            return None
        split = p_string.strip().split("-")
        try:
            params = {p.split("=")[0].strip():p.split("=")[1].strip() for p in split}
        except IndexError:
            print("The given parameters are invalid")
            return None
        return params

    def set_params(self,p_string):
        '''Setter method for parameters that takes a string as input'''
        self.params = self.split_params(p_string)

    def is_empty(self):
        '''Returns True if the SearchQuery object contains no parameters'''
        return self.params is None

    def cache_json(self,name = None):
        '''Saves the recieved JSON file to the current working directory'''
        if name is None:
            name = self._subdir_name() +".json"
        if not name.endswith(".json"):
            name += ".json"
        print(f"Saving {name}...")
        try:
            with open(name, "w",encoding= 'UTF-8') as file:
                file.write(json.dumps(self.json, indent=4))
        except PermissionError:
            print("Failed to write JSON")
        print(f"{name} saved in the current directory.\n")

    def preview(self):
        '''Prints a preview of the results from a GET request'''
        print("\nPreviewing results...")
        counter = 0
        for res in self.results:
            counter += 1
            print(counter,res["title"])
        print("End Preview.\n")

def interactive_demo():
    '''Interactive demo that accepts input for the query from the user'''
    inp = input("Please input your parameters in the form, 'key=value' seperated by a hyphen.\n\
Ex. 'location=Frederick,MD-page=1-stolenness=proximity'\nInput: ")

    ser = SearchQuery()
    ser.set_params(inp)
    res = ser.get()
    if res is None:
        print("No results found. Exiting program...")
        sys.exit()

    print(f"From url: {ser.url}\n")
    name = None
    name_in = input("Would you like to name the subdirectory for the received images?\n\
If yes, please input the name. If not press enter.\nInput: ")

    if name_in != "":
        name = name_in
    ser.save_images(name)
    j_name = None
    json_in = input("Would you like to name the recieved JSON file?\n\
If yes, please input the name. If not press enter.\nInput: ")

    if json_in != "":
        j_name = json_in
    ser.cache_json(j_name)

def demo():
    '''On rails demonstration of the SearchQuery class
    that gets the results of the first 10 bikes in the Chicago area'''
    inp = "page=1-per_page=10-location=Chicago, IL-distance=10-stolenness=proximity"
    ser = SearchQuery()
    ser.set_params(inp)
    ser.get()
    print(f"From url: {ser.url}\n")
    ser.preview()
    ser.cache_json("demo_output.json")
    ser.save_images("demo_output_images")

if __name__ == '__main__':
    OPEN_MESSAGE = 'Would you like to enter the parameters yourself or watch a demonstration?\n\
To watch the demo, press Enter. To input your own parameters, type anything else.\nInput:'

    decision = input(OPEN_MESSAGE)
    if not decision == "":
        interactive_demo()
    else:
        demo()
