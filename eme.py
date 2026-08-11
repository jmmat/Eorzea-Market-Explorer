from flask import Flask, render_template, request

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/search")
def search():
    searched_item = request.args["input-query"]
    return render_template("index.html", searched_item=searched_item)

if __name__ == "__main__":
    app.run()