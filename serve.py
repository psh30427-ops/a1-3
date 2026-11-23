"""Local-only server: static public/ and the same Vercel handler on port 5310."""
import argparse
import os
import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from api.recommend import handler as APIHandler

def load_env():
    path=ROOT/'.env.local'
    if path.exists():
        for line in path.read_text(encoding='utf-8-sig').splitlines():
            line=line.strip()
            if not line or line.startswith('#') or '=' not in line:continue
            key,value=line.split('=',1);key=key.strip()
            if key in {'GEMINI_API_KEY','GEMINI_MODEL','AI_ENABLED','ALLOWED_ORIGIN'}:
                os.environ.setdefault(key,value.strip().strip('\"\''))

class LocalHandler(SimpleHTTPRequestHandler):
    send_json=APIHandler.send_json
    def do_GET(self):
        path=urlparse(self.path).path
        if path=='/api/recommend':return APIHandler.do_GET(self)
        if path.startswith('/api/'):return self.send_json(404,{'error':{'message':'경로를 찾지 못했습니다.'}})
        return super().do_GET()
    def do_POST(self):
        if urlparse(self.path).path=='/api/recommend':return APIHandler.do_POST(self)
        self.send_json(404,{'error':{'message':'경로를 찾지 못했습니다.'}})
    def do_OPTIONS(self):return APIHandler.do_OPTIONS(self)
    def end_headers(self):
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Referrer-Policy','strict-origin-when-cross-origin')
        super().end_headers()
    def log_message(self,*args):pass

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=5310);args=parser.parse_args();load_env()
    server=ThreadingHTTPServer(('127.0.0.1',args.port),partial(LocalHandler,directory=str(ROOT/'public')))
    print(f'Pocket Deck Coach: http://127.0.0.1:{args.port}/',flush=True)
    print('Localhost only. API key values are never logged.',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
if __name__=='__main__':main()

