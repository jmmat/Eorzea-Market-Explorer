from flask import Flask, render_template, request, jsonify
from datetime import datetime
from zoneinfo import ZoneInfo
import requests
import random
from time import perf_counter


app = Flask(__name__)

marketable_item_ids = []
random_item_available = False
WORLDS = [
    "Leviathan",
    "Primal",
    "Behemoth",
    "Excalibur",
    "Exodus",
    "Famfrit",
    "Hyperion",
    "Lamia",
    "Ultros",
    "Aether",
    "Adamantoise",
    "Cactuar",
    "Faerie",
    "Gilgamesh",
    "Jenova",
    "Midgardsormr",
    "Sargatanas",
    "Siren",
    "Crystal",
    "Balmung",
    "Brynhildr",
    "Coeurl",
    "Diabolos",
    "Goblin",
    "Malboro",
    "Mateus",
    "Zalera",
    "Dynamis",
    "Cuchulainn",
    "Halicarnassus",
    "Kraken",
    "Maduin",
    "Marilith",
    "Rafflesia",
    "Seraph"
    ]

@app.context_processor
def inject_random_item_status():
    return {
        "random_item_available": random_item_available,
        "worlds": WORLDS
    }



try:
    start = perf_counter()
    response = requests.get(
        "https://universalis.app/api/v2/marketable",
        timeout=10
    )
    response.raise_for_status()
    print(f"Request took {perf_counter() - start:.3f} seconds")

    marketable_item_ids = response.json()
    random_item_available = len(marketable_item_ids) > 0

except (requests.RequestException, ValueError) as error:
    print(f"Could not load marketable items: {error}")



def format_time(entries):
    for entry in entries:
        entry["timestamp"] = datetime.fromtimestamp(entry["timestamp"], ZoneInfo("America/New_York")).strftime("%m/%d/%Y  %I:%M %p")

def format_hq(entries):
    for entry in entries:
        if entry["hq"]:
            entry["hq"] = "HQ"
        else:
            entry["hq"] = "NQ"


def get_market_data(item_id, world):
    try:
        start = perf_counter()
        item_data = requests.get(
            f"https://v2.xivapi.com/api/sheet/Item/{item_id}",
            timeout=10
        )
        print(f"XIVAPI item sheet request took {perf_counter() - start:.3f} seconds")
        item_data.raise_for_status()
        item_data = item_data.json()
        
        start = perf_counter()
        item_icon_url = requests.get(
            "https://v2.xivapi.com/api/asset",
            params={"path": item_data["fields"]["Icon"]["path"], "format": "png"},
            timeout=10
        ).url
        print(f"XIVAPI asset (image) request took {perf_counter() - start:.3f} seconds")
        if item_data["fields"]["IsUntradable"]:
            return {
                "untradable": True,
                "searched_item": item_data["fields"]["Name"],
                "searched_world": world,
                "item_icon_url": item_icon_url,
            }
        start = perf_counter()
        universalis_response = requests.get(
            f"https://universalis.app/api/v2/{world}/{item_id}",
            timeout=10
        )
        print(f"Universalis request took {perf_counter() - start:.3f} seconds")

        if universalis_response.status_code != 200:
            return {
                "search_error": True,
                "status_code": universalis_response.status_code,
            }

        universalis_data = universalis_response.json()

        item_recent_history = universalis_data["recentHistory"]
        item_current_listings = universalis_data["listings"]

        format_hq(item_recent_history)
        format_hq(item_current_listings)
        format_time(item_recent_history)

        return {
            "searched_item": item_data["fields"]["Name"],
            "searched_world": world,
            "item_icon_url": item_icon_url,
            "item_recent_history": item_recent_history,
            "item_current_listings": item_current_listings,
            "item_id": item_id,
        }

    except requests.exceptions.Timeout:
        return {"timeout": True}

    except requests.exceptions.RequestException as error:
        print(f"API request failed: {error}")
        return {"search_error": True}


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/search")
def search():
    searched_item = request.args.get("input-query", "")
    searched_world = request.args.get("world", "")

    if not searched_item:
        return render_template(
            "index.html",
            searched_world=searched_world
        )

    try:
        start = perf_counter()
        response = requests.get(
            "https://v2.xivapi.com/api/search",
            params={
                "query": f'Name~"{searched_item}"',
                "sheets": ["Item"]
            },
            timeout=10
        )
        response.raise_for_status()
        ffxivapi_response_data = response.json()
        print(f"XIVAPI search request took {perf_counter() - start:.3f} seconds")

    except requests.exceptions.Timeout:
        return render_template("index.html", timeout=True)

    except requests.exceptions.RequestException as error:
        print(f"XIVAPI search failed: {error}")
        return render_template("index.html", search_error=True)

    if not ffxivapi_response_data["results"]:
        return render_template(
            "index.html",
            failed_search=True,
            searched_item=searched_item.title(),
            searched_world=searched_world
        )

    item_id = ffxivapi_response_data["results"][0]["row_id"]

    result = get_market_data(item_id, searched_world)

    return render_template("index.html", **result)


@app.route("/expand-results")
def expand_results():
    searched_item_id = request.args["item_id"]
    searched_world = request.args["world"]
    print("Flask received the request!")
    try:
        start = perf_counter()
        expanded_search = requests.get(f"https://universalis.app/api/v2/{searched_world}/{searched_item_id}", params={"entries": 20}, timeout=10)
        print(f"Universalis request took {perf_counter() - start:.3f} seconds")
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



@app.route("/random")
def random_item():
    random_item_id = random.choice(marketable_item_ids)
    random_world = random.choice(WORLDS)

    result = get_market_data(random_item_id, random_world)

    return render_template("index.html", **result)


@app.route("/flash-test")
def flash_test():

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="color-scheme" content="dark">

        <style>
            html, body {{
                margin: 0;
                min-height: 100%;
                background-color: #101827;
                color: #e9eef7;
            }}
            
            h1 {{
                font-size: 3.5rem;
            }}
        </style>
        <link rel="icon" href="/static/images/ffxivfavicon.png">
        <link rel="stylesheet" href="/static/style.css">
    </head>
    <body>
        <h1>EME Background Test</h1>
        <p>Testing Firefox page reloads.</p>
    </body>
    </html>
    """

@app.route("/flash-test2")
def flash_test2():

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="color-scheme" content="dark">

        <style>
            html, body {{
                margin: 0;
                min-height: 100%;
                color: #e9eef7;
            }}
            
            h1, p {{
                position: relative;
                z-index: 1;
            }}
            
            h1 {{
                font-size: 3.5rem;
            }}
        </style>
        <link rel="preload" as="image" href="/static/images/limsa.jpg">
        <link rel="icon" href="/static/images/ffxivfavicon.png">
        <link rel="stylesheet" href="/static/style.css">
    </head>
    <body>
        <div class="background-image" style="background: url('/static/images/limsa.jpg') center / cover no-repeat; filter: none;"></div>
        
        <h1>EME Background Test</h1>
        <p>Testing Firefox page reloads.</p>
    </body>
    </html>
    """

if __name__ == "__main__":
    app.run()