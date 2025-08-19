from flask import Flask, jsonify
from threading import Thread
import requests
import time
import os
import asyncio
import logging

app = Flask('')
logger = logging.getLogger(__name__)

@app.route('/')
def home():
    return jsonify({
        "status": "alive",
        "message": "Discord Bot is running!",
        "uptime": "24/7 Active"
    })

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "timestamp": time.time()
    })

def run():
    app.run(host='0.0.0.0', port=8080, debug=False)

def ping_self():
    """Ping the server every 5 minutes to keep it alive"""
    while True:
        try:
            time.sleep(300)  # 5 minutes
            repl_url = os.getenv('REPL_URL', 'http://localhost:8080')
            if repl_url != 'http://localhost:8080':
                requests.get(f"{repl_url}/health", timeout=10)
                logger.info("Keep-alive ping sent successfully")
        except Exception as e:
            logger.error(f"Keep-alive ping failed: {e}")

def keep_alive():
    # Start Flask server
    server_thread = Thread(target=run)
    server_thread.daemon = True
    server_thread.start()
    
    # Start keep-alive pinger
    ping_thread = Thread(target=ping_self)
    ping_thread.daemon = True
    ping_thread.start()
    
    logger.info("Keep-alive system started - Bot will stay active 24/7")