from http.server import HTTPServer, SimpleHTTPRequestHandler
import sys

class CustomHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.path = '/index.html'
        return super().do_GET()

def run(port=8080):
    server_address = ('', port)
    httpd = HTTPServer(server_address, CustomHandler)
    print(f'🚀 Server running on port {port}')
    print(f'📁 Serving files from current directory')
    httpd.serve_forever()

if __name__ == '__main__':
    port = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[1] == '--port' else 8080
    run(port)
