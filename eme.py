from flask import Flask, render_template, request
from datetime import datetime
from zoneinfo import ZoneInfo
import requests

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/search")
def search():
    searched_item = request.args["input-query"]
    searched_world = request.args["world"]
    
    if not searched_item:
        return render_template("index.html", searched_world=searched_world)
    
    ffxivapi_response_data = requests.get("https://v2.xivapi.com/api/search", params={"query": f'Name="{searched_item}"', "sheets": ["Item"]}).json()
    if not ffxivapi_response_data["results"]:
        failed_search = True
        return render_template("index.html", failed_search=failed_search, searched_item=searched_item, searched_world=searched_world)
    
    item_id = ffxivapi_response_data["results"][0]["row_id"]
    universalis_response = requests.get(f"https://universalis.app/api/v2/{searched_world}/{item_id}").json()
    
    icon_path = ffxivapi_response_data["results"][0]["fields"]["Icon"]["path"]
    item_icon_url = requests.get(f"https://v2.xivapi.com/api/asset", params={"path": icon_path, "format": "png"}).url
    
    item_recent_history = universalis_response["recentHistory"]
    item_current_listings = universalis_response["listings"]
    
    for purchase in item_recent_history:
        if purchase["hq"]:
            purchase["hq"] = "HQ"
        else:
            purchase["hq"] = "NQ"

    for listing in item_current_listings:
        if listing["hq"]:
            listing["hq"] = "HQ"
        else:
            listing["hq"] = "NQ"
    
    for purchase in item_recent_history:
        purchase["timestamp"] = datetime.fromtimestamp(purchase["timestamp"], ZoneInfo("America/New_York")).strftime("%m/%d/%Y  %I:%M %p")
    
    return render_template("index.html", 
                           searched_item=searched_item, searched_world=searched_world, 
                           item_icon_url=item_icon_url, item_recent_history=item_recent_history,
                           item_current_listings=item_current_listings
                           )

@app.route("/expand-results")
def expand_results():
    return "Flask received the request!"

if __name__ == "__main__":
    app.run()