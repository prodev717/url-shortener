from flask import Flask,request,jsonify,redirect,send_file
from urllib.parse import urlparse
import sqlite3
import random
import string

def generateId():
    return "".join(random.choices(string.ascii_letters+string.digits,k=6))

app = Flask(__name__)

def validateURL(url):
    parsed_url = urlparse(url)
    return bool(parsed_url.scheme and parsed_url.netloc)

def connect2db():
    database = sqlite3.connect("database.db")
    database.row_factory = sqlite3.Row
    return database

with connect2db() as db:
    cursor = db.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS urls (ids TEXT PRIMARY KEY, url TEXT)")
    db.commit()

@app.route("/")
def home():
    return send_file("index.html")

@app.route("/short", methods=["POST"])
def shortener():
    db = connect2db()
    cursor = db.cursor()
    data = request.get_json()
    if not data or "url" not in data:
        return jsonify({"error": "Bad Request", "message": "Missing 'url' in request body."}), 400
    cursor.execute("SELECT ids FROM urls WHERE url = ? ",(data["url"],))
    ids = cursor.fetchone()
    if ids:
        db.close()
        return jsonify({"shortened_url":request.url_root+ids["ids"]}), 200
    else:
        if validateURL(data["url"]):
            newid = generateId()
            cursor.execute("INSERT INTO urls VALUES ( ? , ? )", (newid,data["url"]))
            db.commit()
            db.close()
            return jsonify({"shortened_url":request.url_root+newid}), 200
        else:
            return jsonify({"error": "Invalid URL"}), 400

@app.route("/<ids>")
def expand(ids):
    db = connect2db()
    cursor = db.cursor()
    cursor.execute("SELECT url FROM urls WHERE ids = ? ",(ids,))
    url = cursor.fetchone()
    db.close()
    if url:
        return redirect(url["url"]), 302
    else:
        return jsonify({"error":"URL Not Found"}), 404

if __name__ == '__main__':
    app.run(host="0.0.0.0",port=8000,debug=True)
