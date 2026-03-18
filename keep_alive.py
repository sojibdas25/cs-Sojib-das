from flask import Flask
from threading import Thread

app_web = Flask(__name__)

@app_web.route('/')
def home():
    return "Bot is running!"

@app_web.route('/ping')
def ping():
    return "pong", 200

def run():
    app_web.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()
