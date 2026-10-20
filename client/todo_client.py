"""HTTP client for the waynotes Unix-socket daemon."""

from __future__ import annotations

import json
import os
import socket
from typing import Any


class TodoClient:
    def __init__(self, socket_path: str | None = None) -> None:
        if socket_path is None:
            runtime_dir = os.environ.get("XDG_RUNTIME_DIR")
            if not runtime_dir:
                raise RuntimeError("XDG_RUNTIME_DIR is not set")
            socket_path = os.path.join(runtime_dir, "waynotes-daemon.sock")
        self.socket_path = socket_path

    def _request(
        self,
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
    ) -> Any:
        payload: bytes | None = None
        if body is not None:
            payload = json.dumps(body).encode("utf-8")

        headers = [
            f"{method} {path} HTTP/1.1",
            "Host: localhost",
            "Connection: close",
            "Accept: application/json",
        ]
        if payload is not None:
            headers.append("Content-Type: application/json")
            headers.append(f"Content-Length: {len(payload)}")
        request = ("\r\n".join(headers) + "\r\n\r\n").encode("utf-8")
        if payload is not None:
            request += payload

        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(5)
        try:
            sock.connect(self.socket_path)
            sock.sendall(request)

            data = b""
            while True:
                chunk = sock.recv(65536)
                if not chunk:
                    break
                data += chunk
        except FileNotFoundError as exc:
            raise ConnectionError(
                "waynotes daemon is not running"
            ) from exc
        except OSError as exc:
            raise ConnectionError(str(exc)) from exc
        finally:
            sock.close()

        if not data:
            raise ConnectionError("empty response from daemon")

        header_bytes, _, body_bytes = data.partition(b"\r\n\r\n")
        status_line = header_bytes.split(b"\r\n", 1)[0]
        try:
            status = int(status_line.split()[1])
        except (IndexError, ValueError) as exc:
            raise ConnectionError("invalid HTTP response") from exc

        if status == 204:
            return None

        try:
            parsed = json.loads(body_bytes.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ConnectionError("invalid JSON from daemon") from exc

        if status >= 400:
            message = (
                parsed.get("error", f"HTTP {status}")
                if isinstance(parsed, dict)
                else f"HTTP {status}"
            )
            raise RuntimeError(message)

        return parsed

    def health(self) -> dict[str, str]:
        result = self._request("GET", "/api/v1/health")
        assert isinstance(result, dict)
        return result

    def count(self) -> dict[str, int]:
        result = self._request("GET", "/api/v1/todos/count")
        assert isinstance(result, dict)
        return result

    def list_todos(self) -> list[dict[str, Any]]:
        result = self._request("GET", "/api/v1/todos")
        assert isinstance(result, dict)
        todos = result.get("todos", [])
        if not isinstance(todos, list):
            raise RuntimeError("unexpected list response")
        return todos

    def create(self, title: str) -> dict[str, Any]:
        result = self._request(
            "POST",
            "/api/v1/todos",
            {"title": title},
        )
        assert isinstance(result, dict)
        return result

    def update(
        self,
        todo_id: str,
        *,
        title: str | None = None,
        completed: bool | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {}
        if title is not None:
            body["title"] = title
        if completed is not None:
            body["completed"] = completed

        result = self._request("PATCH", f"/api/v1/todos/{todo_id}", body)
        assert isinstance(result, dict)
        return result

    def delete(self, todo_id: str) -> None:
        self._request("DELETE", f"/api/v1/todos/{todo_id}")
