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
    print(searched_item)
    searched_world = request.args["world"]
    print(searched_world)
    ffxivapi_response_data = requests.get("https://v2.xivapi.com/api/search", params={"query": f'Name="{searched_item}"', "sheets": ["Item"]}).json()
    print(ffxivapi_response_data["results"][0]["row_id"])
    item_id = ffxivapi_response_data["results"][0]["row_id"]
    universalis_response = requests.get(f"https://universalis.app/api/v2/{searched_world}/{item_id}").json()
    icon_path = ffxivapi_response_data["results"][0]["fields"]["Icon"]["path"]
    item_icon_url = requests.get(f"https://v2.xivapi.com/api/asset", params={"path": icon_path, "format": "png"}).url
    return render_template("index.html", searched_item=searched_item, searched_world=searched_world, item_icon_url=item_icon_url)

if __name__ == "__main__":
    app.run()