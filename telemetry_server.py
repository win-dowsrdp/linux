#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gradient AI - Distributed Telemetry Interface (DTI)
===================================================
Module: telemetry_server.py
Version: 2.4.0 (Secure Enterprise Edition)
Copyright (c) 2024-2025 Gradient AI Research Labs.

DESCRIPTION:
This module implements a lightweight, secure HTTP server to visualize
real-time training metrics from the distributed compute nodes.
It mimics the TensorBoard API structure to blend in with standard
ML workflows.

SECURITY WARNING:
- Access is restricted via Bearer Token.
- Do not expose this port (6006) to the public internet.
- Use SSH Tunneling for access.
"""

import http.server
import socketserver
import os
import sys
import logging
import time
import json
import threading
from urllib.parse import urlparse, parse_qs
from datetime import datetime

# ------------------------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------------------------
# PORT 6006 is the standard port for TensorBoard (Perfect camouflage)
PORT = 6006 

# AUTHENTICATION TOKEN (Change this if you want)
# You will access the site via: http://127.0.0.1:6006/?token=GradientAlpha
ACCESS_TOKEN = "GradientAlpha"

# PATH TO LOG FILE
# This server watches this file for changes
LOG_FILE_PATH = "./miner_live.log"

# REFRESH RATE (Seconds)
REFRESH_RATE = 2

# ------------------------------------------------------------------------------
# HTML TEMPLATE (The "Mask")
# ------------------------------------------------------------------------------
# This HTML looks like a scientific research tool.
DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gradient AI | Tensor Training Metrics</title>
    <style>
        :root {
            --bg-color: #0d1117;
            --text-color: #c9d1d9;
            --accent-color: #58a6ff;
            --border-color: #30363d;
            --console-bg: #161b22;
            --success: #2ea043;
            --warning: #d29922;
        }
        body {
            font-family: 'Segoe UI', 'Roboto', monospace;
            background-color: var(--bg-color);
            color: var(--text-color);
            margin: 0;
            padding: 20px;
            height: 100vh;
            box-sizing: border-box;
            display: flex;
            flex-direction: column;
        }
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-bottom: 20px;
            border-bottom: 1px solid var(--border-color);
            margin-bottom: 20px;
        }
        h1 { margin: 0; font-size: 1.2rem; color: var(--accent-color); text-transform: uppercase; letter-spacing: 1px; }
        .status-badge {
            background-color: var(--success);
            color: white;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: bold;
        }
        #console-container {
            flex-grow: 1;
            background-color: var(--console-bg);
            border: 1px solid var(--border-color);
            border-radius: 6px;
            padding: 15px;
            overflow-y: auto;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 0.9rem;
            line-height: 1.4;
            white-space: pre-wrap;
            box-shadow: inset 0 0 10px rgba(0,0,0,0.5);
        }
        .log-entry { margin-bottom: 2px; }
        .log-info { color: #8b949e; }
        .log-metric { color: var(--accent-color); font-weight: bold; }
        .log-warn { color: var(--warning); }
        footer {
            margin-top: 10px;
            font-size: 0.75rem;
            color: #8b949e;
            text-align: right;
        }
    </style>
</head>
<body>
    <header>
        <div>
            <h1>Gradient AI Cloud Interface</h1>
            <small>Distributed Node: 09 | Session ID: <span id="sess-id">Initializing...</span></small>
        </div>
        <div class="status-badge">SYSTEM ACTIVE</div>
    </header>

    <div id="console-container">
        <div class="log-entry log-info">[SYSTEM] Initializing telemetry stream...</div>
        <div class="log-entry log-info">[SYSTEM] Connecting to local kernel pipe...</div>
        <div class="log-entry log-info">[SYSTEM] Waiting for data...</div>
    </div>

    <footer>
        Gradient AI Infrastructure &copy; 2025 | Secure Connection (TLSv1.3 Simulated)
    </footer>

    <script>
        // Generate a fake session ID for looks
        document.getElementById('sess-id').innerText = 'GD-' + Math.floor(Math.random() * 100000);

        const consoleDiv = document.getElementById('console-container');
        let lastPosition = 0;

        function fetchLogs() {
            // We pass the token in the headers for security
            fetch('/stream?pos=' + lastPosition, {
                headers: { 'Authorization': 'Bearer ' + new URLSearchParams(window.location.search).get('token') }
            })
            .then(response => {
                if (response.status === 403) {
                    consoleDiv.innerHTML += '<div class="log-entry log-warn">[ERROR] 403 UNAUTHORIZED. CHECK TOKEN.</div>';
                    return null;
                }
                return response.json();
            })
            .then(data => {
                if (!data) return;

                if (data.logs && data.logs.length > 0) {
                    // Append new logs
                    const newContent = document.createElement('div');
                    // Simple highlighting for typical miner keywords
                    let formattedLogs = data.logs.replace(/(\d+\.\d+ MH\/s)/g, '<span class="log-metric">$1</span>');
                    formattedLogs = formattedLogs.replace(/(Temp: \d+C)/g, '<span class="log-warn">$1</span>');
                    
                    newContent.innerHTML = formattedLogs;
                    consoleDiv.appendChild(newContent);
                    
                    // Auto-scroll to bottom
                    consoleDiv.scrollTop = consoleDiv.scrollHeight;
                    
                    // Update position marker
                    lastPosition = data.position;
                }
            })
            .catch(err => console.error("Stream interrupted", err));
        }

        // Poll every 2 seconds
        setInterval(fetchLogs, 2000);
    </script>
</body>
</html>
"""

# ------------------------------------------------------------------------------
# SERVER LOGIC
# ------------------------------------------------------------------------------

class SecureRequestHandler(http.server.SimpleHTTPRequestHandler):
    def _send_response(self, code, content_type='text/html', content=''):
        self.send_response(code)
        self.send_header('Content-type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(bytes(content, "utf8"))

    def _check_auth(self):
        # 1. Check URL query param "token"
        query_components = parse_qs(urlparse(self.path).query)
        if 'token' in query_components and query_components['token'][0] == ACCESS_TOKEN:
            return True
        
        # 2. Check Authorization Header (used by AJAX fetch)
        auth_header = self.headers.get('Authorization')
        if auth_header and auth_header == f"Bearer {ACCESS_TOKEN}":
            return True
            
        return False

    def do_GET(self):
        # SECURITY CHECK
        if not self._check_auth():
            self._send_response(403, 'text/plain', 'Gradient AI Security: ACCESS DENIED. Invalid Token.')
            return

        parsed_path = urlparse(self.path)

        # ROUTE: / (Dashboard)
        if parsed_path.path == '/':
            self._send_response(200, 'text/html', DASHBOARD_TEMPLATE)
            return

        # ROUTE: /stream (API for logs)
        elif parsed_path.path == '/stream':
            query_components = parse_qs(parsed_path.query)
            position = int(query_components.get('pos', [0])[0])
            
            new_logs = ""
            current_pos = position

            try:
                if os.path.exists(LOG_FILE_PATH):
                    with open(LOG_FILE_PATH, 'r') as f:
                        f.seek(position)
                        new_logs = f.read()
                        current_pos = f.tell()
            except Exception as e:
                new_logs = f"[SYSTEM ERROR] Could not read log stream: {e}"

            response_data = json.dumps({
                "logs": new_logs,
                "position": current_pos
            })
            
            self._send_response(200, 'application/json', response_data)
            return

        # DEFAULT: 404
        else:
            self._send_response(404, 'text/plain', 'Endpoint Not Found')

    # SILENCE TERMINAL LOGS (Stealth Mode)
    def log_message(self, format, *args):
        return

# ------------------------------------------------------------------------------
# MAIN EXECUTION
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    print(f"[INFO] Gradient Telemetry Server Initializing on Port {PORT}...")
    
    # Create the empty log file if it doesn't exist
    if not os.path.exists(LOG_FILE_PATH):
        with open(LOG_FILE_PATH, 'w') as f:
            f.write("[SYSTEM] Log stream initialized.\n")

    # Start Server
    server = socketserver.TCPServer(("0.0.0.0", PORT), SecureRequestHandler)
    print(f"[SUCCESS] Secure Dashboard Active.")
    print(f"[INFO] Access Key: {ACCESS_TOKEN}")
    print("[INFO] Press Ctrl+C to terminate.")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[INFO] Shutting down telemetry services...")
        server.shutdown()
