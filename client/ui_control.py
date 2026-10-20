"""Single-instance control socket for the Waynotes panel."""

from __future__ import annotations

import os

from PyQt6.QtNetwork import QLocalServer, QLocalSocket


def control_socket_path() -> str:
    runtime_dir = os.environ.get("XDG_RUNTIME_DIR")
    if not runtime_dir:
        raise RuntimeError("XDG_RUNTIME_DIR is not set")
    return os.path.join(runtime_dir, "waynotes-ui-control.sock")


def send_toggle(timeout_ms: int = 200) -> bool:
    """Ask a running panel to toggle. Returns True if the panel handled it."""
    socket = QLocalSocket()
    socket.connectToServer(control_socket_path())

    if not socket.waitForConnected(timeout_ms):
        return False

    socket.write(b"toggle\n")
    socket.waitForBytesWritten(timeout_ms)
    socket.disconnectFromServer()
    return True


def listen_for_toggle(on_toggle) -> QLocalServer:
    """Start the control server; calls ``on_toggle`` for each toggle command."""
    server_name = control_socket_path()
    server = QLocalServer()
    QLocalServer.removeServer(server_name)

    if not server.listen(server_name):
        raise RuntimeError(
            f"Cannot start UI control server: {server.errorString()}"
        )

    try:
        os.chmod(server_name, 0o600)
    except OSError:
        pass

    def handle_connection() -> None:
        client = server.nextPendingConnection()
        if client is None:
            return

        def handle_data() -> None:
            command = bytes(client.readAll()).decode(
                "utf-8", errors="replace"
            ).strip()
            if command == "toggle":
                on_toggle()
            client.disconnectFromServer()

        client.readyRead.connect(handle_data)

    server.newConnection.connect(handle_connection)
    return server
