#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gradient AI - Distributed Telemetry Interface (DTI)
===================================================
Module: telemetry_server.py
Version: 3.0.0 (Ghost Protocol - In-Memory)
"""

import http.server
import socketserver
import socket
import threading
import json
import collections
from urllib.parse import urlparse, parse_qs

# ------------------------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------------------------
HTTP_PORT = 6006           # Dashboard Port
UDP_PORT = 65000           # Secret Internal Data Port
ACCESS_TOKEN = "GradientAlpha"
MAX_LOG_LINES = 200        # Keep last 200 lines in RAM

# ------------------------------------------------------------------------------
# IN-MEMORY LOG BUFFER (NO DISK FILES)
# ------------------------------------------------------------------------------
# This deque stores logs in RAM only. If the script stops, logs vanish.
log_buffer = collections.deque(maxlen=MAX_LOG_LINES)
buffer_lock = threading.Lock()

def udp_listener():
    """
    Background thread that catches log packets flying through localhost.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('127.0.0.1', UDP_PORT))
    print(f"[SYSTEM] Ghost Listener Active on UDP :{UDP_PORT}")
    
    while True:
        try:
            data, _ = sock.recvfrom(4096) # Buffer size 4KB
            line = data.decode('utf-8', errors='ignore')
            
            with buffer_lock:
                log_buffer.append(line)
        except Exception as e:
            print(f"UDP Error: {e}")

# ------------------------------------------------------------------------------
# HTML DASHBOARD (SAME VISUALS)
# ------------------------------------------------------------------------------
DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Gradient AI | Ghost Node</title>
    <style>
        body { background: #0d1117; color: #c9d1d9; font-family: monospace; padding: 20px; }
        #console { background: #161b22; padding: 15px; border: 1px solid #30363d; height: 80vh; overflow-y: scroll; white-space: pre-wrap; }
        .metric { color: #58a6ff; font-weight: bold; }
        .warn { color: #d29922; }
    </style>
</head>
<body>
    <h3>Gradient AI | Secure Telemetry (RAM-Only)</h3>
    <div id="console">Waiting for stream...</div>
    <script>
        const consoleDiv = document.getElementById('console');
        
        function fetchLogs() {
            fetch('/stream', { headers: { 'Authorization': 'Bearer ' + new URLSearchParams(window.location.search).get('token') } })
            .then(res => res.json())
            .then(data => {
                // Clear and replace content (Simple refresh)
                if(data.logs) {
                    // Highlight metrics for readability
                    let html = data.logs.replace(/(\\d+\\.\\d+ MH\\/s)/g, '<span class="metric">$1</span>');
                    html = html.replace(/(Temp: \\d+C)/g, '<span class="warn">$1</span>');
                    consoleDiv.innerHTML = html;
                    consoleDiv.scrollTop = consoleDiv.scrollHeight;
                }
            });
        }
        setInterval(fetchLogs, 2000);
    </script>
</body>
</html>
"""

# ------------------------------------------------------------------------------
# HTTP HANDLER
# ------------------------------------------------------------------------------
class GhostRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Auth Check
        token = parse_qs(urlparse(self.path).query).get('token', [''])[0]
        if token != ACCESS_TOKEN:
            self.send_response(403); self.end_headers(); return

        if self.path.startswith('/stream'):
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            with buffer_lock:
                # Send all current RAM logs joined as a string
                full_log = "".join(list(log_buffer))
            
            self.wfile.write(json.dumps({"logs": full_log}).encode())
            return

        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(DASHBOARD_TEMPLATE.encode())
    
    def log_message(self, format, *args): return # Silence

if __name__ == "__main__":
    # Start UDP Listener Thread
    t = threading.Thread(target=udp_listener, daemon=True)
    t.start()
    
    # Start HTTP Server
    server = socketserver.TCPServer(("0.0.0.0", HTTP_PORT), GhostRequestHandler)
    try: server.serve_forever()
    except: pass
