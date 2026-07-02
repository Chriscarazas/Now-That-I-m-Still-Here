#!/usr/bin/env python3
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import os, socket, threading, webbrowser

ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)

class NoCacheHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

port = 8161
server = ThreadingHTTPServer(('127.0.0.1', port), NoCacheHandler)
url = f'http://127.0.0.1:{port}/?build=v6.6'
print(f'Preview running at {url}')
print('Press Control+C to stop the preview server.')
threading.Timer(0.5, lambda: webbrowser.open(url)).start()
try:
    server.serve_forever()
except KeyboardInterrupt:
    print('\nPreview stopped.')
finally:
    server.server_close()
