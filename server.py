#!/usr/bin/env python3
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import tempfile
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import unquote
import webbrowser

ROOT = Path(__file__).resolve().parent
def downloads_directory():
    if os.environ.get('GIF_MP4_DOWNLOADS'):
        return Path(os.environ['GIF_MP4_DOWNLOADS']).expanduser().resolve()
    if sys.platform == 'win32':
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                r'Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders') as key:
            value, _ = winreg.QueryValueEx(key, '{374DE290-123F-4565-9164-39C4925E467B}')
            return Path(os.path.expandvars(value))
    if sys.platform.startswith('linux') and shutil.which('xdg-user-dir'):
        result = subprocess.run(['xdg-user-dir', 'DOWNLOAD'], capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            return Path(result.stdout.strip())
    return Path.home() / 'Downloads'

DOWNLOADS = downloads_directory()
TOKEN = secrets.token_urlsafe(32)
FFMPEG = os.environ.get('FFMPEG_BINARY') or shutil.which('ffmpeg')
PORT = 18746

class Handler(BaseHTTPRequestHandler):
    def respond(self, status, data, kind='application/json; charset=utf-8'):
        body = data.encode() if isinstance(data, str) else json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', kind)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == '/':
            self.respond(200, (ROOT / 'index.html').read_text().replace('__TOKEN__', TOKEN), 'text/html; charset=utf-8')
        elif self.path == '/health':
            self.respond(200, {'app': 'local-gif-mp4'})
        else:
            self.respond(404, {'error': '页面不存在'})

    def do_POST(self):
        if self.headers.get('X-Token') != TOKEN:
            return self.respond(403, {'error': '请刷新页面后重试'})
        if self.path == '/folder':
            try:
                DOWNLOADS.mkdir(parents=True, exist_ok=True)
                if sys.platform == 'win32':
                    os.startfile(str(DOWNLOADS))
                else:
                    subprocess.Popen(['open' if sys.platform == 'darwin' else 'xdg-open', str(DOWNLOADS)])
                return self.respond(200, {'ok': True})
            except OSError as error:
                return self.respond(400, {'error': str(error)})
        if self.path != '/convert':
            return self.respond(404, {'error': '接口不存在'})
        output = None
        try:
            size = int(self.headers.get('Content-Length', '0'))
            name = Path(unquote(self.headers.get('X-Filename', 'animation.gif')).replace('\\', '/')).name
            if not name.lower().endswith('.gif') or size < 6:
                raise ValueError('请选择有效的 GIF 文件')
            with tempfile.TemporaryDirectory(prefix='gif-mp4-') as temp:
                source = Path(temp) / 'input.gif'
                with source.open('wb') as target:
                    remaining = size
                    while remaining:
                        chunk = self.rfile.read(min(1024 * 1024, remaining))
                        if not chunk:
                            raise ValueError('文件传输中断，请重试')
                        target.write(chunk)
                        remaining -= len(chunk)
                with source.open('rb') as stream:
                    if stream.read(6) not in (b'GIF87a', b'GIF89a'):
                        raise ValueError('文件内容不是 GIF')
                DOWNLOADS.mkdir(parents=True, exist_ok=True)
                stem = Path(name).stem
                index = 0
                while True:
                    output = DOWNLOADS / (f'{stem}.mp4' if index == 0 else f'{stem} ({index}).mp4')
                    try:
                        fd = os.open(output, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
                        os.close(fd)
                        break
                    except FileExistsError:
                        index += 1
                result = subprocess.run([FFMPEG, '-hide_banner', '-loglevel', 'error', '-y',
                    '-ignore_loop', '1', '-i', str(source), '-an',
                    '-vf', 'pad=ceil(iw/2)*2:ceil(ih/2)*2:color=white',
                    '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
                    '-pix_fmt', 'yuv420p', '-fps_mode', 'vfr', '-movflags', '+faststart', str(output)],
                    capture_output=True, text=True)
                if result.returncode:
                    raise ValueError('转换失败：' + result.stderr[-500:])
                self.respond(200, {'name': output.name, 'path': str(output), 'bytes': output.stat().st_size})
        except Exception as error:
            if output is not None:
                output.unlink(missing_ok=True)
            self.respond(400, {'error': str(error)})

if __name__ == '__main__':
    if not FFMPEG or not Path(FFMPEG).is_file():
        raise SystemExit('FFmpeg not found. Install FFmpeg and add it to PATH; see README.md.')
    try:
        server = HTTPServer(('127.0.0.1', PORT), Handler)
    except OSError:
        import urllib.request
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(f'http://127.0.0.1:{PORT}/health', timeout=2) as response:
            if json.load(response).get('app') != 'local-gif-mp4':
                raise SystemExit('端口被其他程序占用')
        webbrowser.open(f'http://127.0.0.1:{PORT}')
        raise SystemExit()
    webbrowser.open(f'http://127.0.0.1:{PORT}')
    print(f'GIF → MP4: http://127.0.0.1:{PORT}\nOutput: {DOWNLOADS}\nPress Ctrl+C to stop.', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
