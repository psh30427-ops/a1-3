"""Vercel file-based Python function: /api/recommend."""
import hashlib
import json
import os
import threading
import time
from collections import defaultdict, deque
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse
from backend.coach import CoachError, MAX_BODY, recommend

_lock=threading.Lock()
_hits=defaultdict(deque)

def check_rate(identity):
    now=time.monotonic()
    with _lock:
        # This is per-process throttling, not a durable global quota.
        for key in list(_hits):
            while _hits[key] and now-_hits[key][0]>60: _hits[key].popleft()
            if not _hits[key]: del _hits[key]
        key=hashlib.sha256(identity.encode()).hexdigest()[:16]
        if len(_hits[key])>=5:
            raise CoachError('rate_limited','요청이 너무 빠릅니다. 1분 뒤 다시 시도해 주세요.',429)
        if len(_hits)>1000:
            raise CoachError('busy','이용자가 많습니다. 잠시 후 다시 시도해 주세요.',503)
        _hits[key].append(now)

class handler(BaseHTTPRequestHandler):
    def send_json(self,status,payload):
        body=json.dumps(payload,ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        if status==429: self.send_header('Retry-After','60')
        self.send_header('Content-Length',str(len(body)))
        self.end_headers()
        try:self.wfile.write(body)
        except (BrokenPipeError,ConnectionResetError):pass

    def do_GET(self):
        ready=bool(os.environ.get('GEMINI_API_KEY','').strip()) and os.environ.get('AI_ENABLED','true').lower()=='true'
        self.send_json(200,{'ready':ready,'mode':'live' if ready else 'unconfigured'})

    def do_POST(self):
        try:
            origin=self.headers.get('Origin')
            host=self.headers.get('Host','')
            allowed=os.environ.get('ALLOWED_ORIGIN','').rstrip('/')
            if origin and (urlparse(origin).netloc!=host if not allowed else origin.rstrip('/')!=allowed):
                raise CoachError('origin_blocked','이 사이트에서 다시 요청해 주세요.',403)
            if self.headers.get_content_type()!='application/json':
                raise CoachError('invalid_type','JSON 형식의 입력이 필요합니다.',415)
            try:length=int(self.headers.get('Content-Length','0'))
            except ValueError:raise CoachError('invalid_body','입력 크기를 확인해 주세요.')
            if not 0<length<=MAX_BODY:raise CoachError('too_large','입력이 비어 있거나 너무 깁니다.',413)
            try:value=json.loads(self.rfile.read(length))
            except (ValueError,UnicodeDecodeError):raise CoachError('invalid_json','입력 형식을 확인해 주세요.')
            check_rate(self.client_address[0])
            self.send_json(200,recommend(value))
        except CoachError as error:
            self.send_json(error.status,{'error':{'code':error.code,'message':error.message}})
        except Exception:
            # Never expose provider responses, input content, headers or secrets.
            self.send_json(500,{'error':{'code':'internal_error','message':'일시적인 문제가 생겼습니다. 잠시 후 다시 시도해 주세요.'}})

    def do_OPTIONS(self):self.send_json(405,{'error':{'code':'method_not_allowed','message':'허용되지 않은 요청입니다.'}})
    def do_PUT(self):self.do_OPTIONS()
    def do_DELETE(self):self.do_OPTIONS()
    def log_message(self,*args):pass

