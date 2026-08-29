from flask import Flask, render_template, request, jsonify
from datetime import datetime
from zoneinfo import ZoneInfo
import requests

app = Flask(__name__)

def format_time(entries):
    for entry in entries:
        entry["timestamp"] = datetime.fromtimestamp(entry["timestamp"], ZoneInfo("America/New_York")).strftime("%m/%d/%Y  %I:%M %p")

def format_hq(entries):
    for entry in entries:
        if entry["hq"]:
            entry["hq"] = "HQ"
        else:
            entry["hq"] = "NQ"

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
        return render_template("index.html", failed_search=True, searched_item=searched_item, searched_world=searched_world)
    
    item_id = ffxivapi_response_data["results"][0]["row_id"]
    try:
        universalis_response = requests.get(f"https://universalis.app/api/v2/{searched_world}/{item_id}", timeout=10)
    except requests.exceptions.Timeout:
        return render_template("index.html", timeout=True)
        
    
    print("Status: ", universalis_response.status_code)

    if universalis_response.status_code != 200:
        return render_template("index.html", search_error=True, status_code=universalis_response.status_code)
    
    universalis_response = universalis_response.json()
    
    icon_path = ffxivapi_response_data["results"][0]["fields"]["Icon"]["path"]
    item_icon_url = requests.get(f"https://v2.xivapi.com/api/asset", params={"path": icon_path, "format": "png"}).url
    
    item_recent_history = universalis_response["recentHistory"]
    item_current_listings = universalis_response["listings"]
    
    format_hq(item_recent_history)
    format_hq(item_current_listings)
    
    format_time(item_recent_history)
    
    return render_template("index.html", 
                           searched_item=searched_item, searched_world=searched_world, 
                           item_icon_url=item_icon_url, item_recent_history=item_recent_history,
                           item_current_listings=item_current_listings, item_id=item_id
                           )

@app.route("/expand-results")
def expand_results():
    searched_item_id = request.args["item_id"]
    searched_world = request.args["world"]
    print("Flask received the request!")
    try:
        expanded_search = requests.get(f"https://universalis.app/api/v2/{searched_world}/{searched_item_id}", params={"entries": 20}, timeout=10)
    except requests.exceptions.Timeout:
        return jsonify({
            "timeout": True,
        })

    
    print("Status: ", expanded_search.status_code)

    if expanded_search.status_code != 200:
        return jsonify({
            "error": True,
            "status_code": expanded_search.status_code
        })
    
    expanded_search = expanded_search.json()
    
    format_hq(expanded_search["recentHistory"])
    format_time(expanded_search["recentHistory"])
        
    
    return jsonify(expanded_search)

if __name__ == "__main__":
    app.run()