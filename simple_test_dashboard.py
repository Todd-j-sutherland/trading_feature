import http.server
import socketserver
import json
import sqlite3
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PORT = 8086

class TestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html = '''<html><body><h1>Database Test</h1><button onclick="fetch('/api/test').then(r=>r.json()).then(d=>document.getElementById('result').innerHTML=JSON.stringify(d,null,2))">Test DB</button><pre id="result"></pre></body></html>'''
            self.wfile.write(html.encode())
        elif self.path == '/api/test':
            try:
                conn = sqlite3.connect('enhanced_trading_data.db')
                cursor = conn.cursor()
                count = cursor.execute('SELECT COUNT(*) FROM predictions').fetchone()[0]
                predictions = cursor.execute('SELECT * FROM predictions LIMIT 3').fetchall()
                conn.close()
                
                result = {'status': 'success', 'count': count, 'samples': predictions}
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode())

if __name__ == '__main__':
    with socketserver.TCPServer(('', PORT), TestHandler) as httpd:
        logger.info(f'Test dashboard on port {PORT}')
        httpd.serve_forever()
