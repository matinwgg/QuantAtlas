#!/usr/bin/env python3
"""Simple HTTP callback receiver for demoing training webhooks.

Usage:
  python backend/scripts/callback_receiver.py --port 9090

Receives POST requests and prints the JSON payload to stdout.
"""
import json
import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length)
        try:
            data = json.loads(body)
        except Exception:
            data = body.decode('utf-8', errors='ignore')

        print("\n=== Callback received ===")
        print(data)
        print("=======================\n")

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'OK')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=9090)
    args = parser.parse_args()
    server = HTTPServer(('0.0.0.0', args.port), Handler)
    print(f"Callback receiver listening on http://0.0.0.0:{args.port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down")
        server.server_close()


if __name__ == '__main__':
    main()
