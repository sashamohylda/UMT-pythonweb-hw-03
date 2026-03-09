import mimetypes
import json
import os
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from jinja2 import Environment, FileSystemLoader

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STORAGE_PATH = os.path.join(BASE_DIR, 'storage', 'data.json')


def get_messages():
    if not os.path.exists(STORAGE_PATH):
        return {}
    with open(STORAGE_PATH, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except:
            return {}


def save_message(username, message):
    data = get_messages()
    key = str(datetime.now())
    data[key] = {"username": username, "message": message}
    with open(STORAGE_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class Handler(BaseHTTPRequestHandler):

    def send_html(self, filename, status=200):
        filepath = os.path.join(BASE_DIR, filename)
        if not os.path.exists(filepath):
            self.send_error_page()
            return
        with open(filepath, 'rb') as f:
            content = f.read()
        self.send_response(status)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(content)

    def send_static(self):
        filepath = BASE_DIR + self.path
        if not os.path.exists(filepath):
            self.send_error_page()
            return
        mime, _ = mimetypes.guess_type(filepath)
        with open(filepath, 'rb') as f:
            content = f.read()
        self.send_response(200)
        self.send_header('Content-Type', mime or 'application/octet-stream')
        self.end_headers()
        self.wfile.write(content)

    def send_error_page(self):
        self.send_html('error.html', status=404)

    def send_read_page(self):
        env = Environment(loader=FileSystemLoader(os.path.join(BASE_DIR, 'templates')))
        template = env.get_template('read.html')
        messages = get_messages()
        content = template.render(messages=messages)
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(content.encode('utf-8'))

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == '/':
            self.send_html('index.html')
        elif path == '/message':
            self.send_html('message.html')
        elif path == '/read':
            self.send_read_page()
        elif path.startswith('/static/'):
            self.send_static()
        else:
            self.send_error_page()

    def do_POST(self):
        if self.path == '/message':
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length).decode('utf-8')
            params = parse_qs(body)
            username = params.get('username', [''])[0]
            message = params.get('message', [''])[0]
            save_message(username, message)
            self.send_response(302)
            self.send_header('Location', '/')
            self.end_headers()
        else:
            self.send_error_page()

    def log_message(self, format, *args):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {args[0]} {args[1]}")


if __name__ == '__main__':
    os.makedirs(os.path.join(BASE_DIR, 'storage'), exist_ok=True)
    server = HTTPServer(('', 3000), Handler)
    print("✅ Сервер запущено: http://localhost:3000")
    server.serve_forever()