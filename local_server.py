"""Run Mind Map Wizard locally with shared, disk-backed map history."""

from __future__ import annotations

import json
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DATA_FILE = ROOT / "local-data" / "mindmap-history.json"


def read_history() -> list[dict]:
    try:
        data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def write_history(history: list[dict]) -> None:
    DATA_FILE.parent.mkdir(exist_ok=True)
    DATA_FILE.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")


class AppHandler(SimpleHTTPRequestHandler):
    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Access-Control-Allow-Methods", "GET, PUT, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _is_history_request(self) -> bool:
        return self.path.split("?", 1)[0] == "/api/mindmap-history"

    def _send_json(self, status: HTTPStatus, data: object) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self._is_history_request():
            self._send_json(HTTPStatus.OK, read_history())
            return
        super().do_GET()

    def do_PUT(self) -> None:
        if not self._is_history_request():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        length = int(self.headers.get("Content-Length", "0"))
        try:
            history = json.loads(self.rfile.read(length))
        except json.JSONDecodeError:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Expected a JSON array."})
            return
        if not isinstance(history, list):
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Expected a JSON array."})
            return
        write_history(history[:100])
        self._send_json(HTTPStatus.OK, history[:100])


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 8001), AppHandler)
    print("Mind Map Wizard is running at http://127.0.0.1:8001")
    server.serve_forever()