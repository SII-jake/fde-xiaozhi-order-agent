"""Local browser interface for the order investigation agent."""
import argparse
import json
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from .app import run, configure_logging
from .mock_latency import configure as configure_mock_latency
from .client import MockClient, APIClient
from .config import load_config, DEFAULT_CONFIG
from .tools import ORDERS

PAGE = Path(__file__).with_name('web.html')

def main():
    configure_logging()
    parser = argparse.ArgumentParser(description='Launch the order agent browser app')
    parser.add_argument('--config', default=str(DEFAULT_CONFIG))
    parser.add_argument('--port', type=int, default=8080)
    args = parser.parse_args()
    config = load_config(args.config)
    configure_mock_latency(config["mock"])
    class Handler(BaseHTTPRequestHandler):
        def send(self, status, payload, kind='application/json; charset=utf-8'):
            body = payload if isinstance(payload, bytes) else json.dumps(payload, ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header('Content-Type', kind)
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        def do_GET(self):
            if self.path == '/':
                self.send(200, PAGE.read_bytes(), 'text/html; charset=utf-8')
            elif self.path == '/api/status':
                self.send(200, {'backend': config['llm']['backend'], 'orders': list(ORDERS), 'details': ORDERS})
            else:
                self.send(404, {'error': 'Not found'})
        def do_POST(self):
            if self.path != '/api/investigate':
                self.send(404, {'error': 'Not found'}); return
            try:
                size = int(self.headers.get('Content-Length', 0))
                if not 0 < size <= 4096:
                    raise ValueError('Invalid request size')
                payload = json.loads(self.rfile.read(size))
                order = payload.get('order')
                message = payload.get('message', '')
                if not isinstance(message, str) or len(message) > 2000:
                    raise ValueError('Invalid message')
                if order not in ORDERS:
                    raise ValueError('Unknown order')
                llm = config['llm']
                path = Path(config['tracing']['directory']) / (str(uuid.uuid4()) + '.jsonl')
                client = MockClient(order) if llm['backend'] == 'mock' else APIClient(llm['base_url'], llm['timeout_seconds'])
                tool_events = []
                answer = run(client, order, path, 'teaching-mock' if llm['backend'] == 'mock' else llm['model'], config['agent']['max_turns'], llm['temperature'], llm['max_tokens'], user_message=f'订单编号：{order}。{message}' if message else None, on_tool=tool_events.append)
                self.send(200, {'answer': answer, 'tools': tool_events, 'trace': path.name if path.exists() else None})
            except ValueError as exc:
                self.send(400, {'error': str(exc)})
            except Exception:
                self.send(500, {'error': 'Investigation failed. Check the server console and model configuration.'})
                import traceback
                traceback.print_exc()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    print(f'Order agent: http://127.0.0.1:{args.port}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()

if __name__ == '__main__':
    main()
