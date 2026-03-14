from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from lib.logger import log
from api.auth import get_current_user_from_websocket
import asyncio
import paramiko
import os
import functools
from typing import Optional

router = APIRouter()

log = log()

async def run_in_thread(func, *args, **kwargs):
    """runs a synchronous function in a separate thread."""
    loop = asyncio.get_running_loop()
    if kwargs:
        func = functools.partial(func, **kwargs)
    return await loop.run_in_executor(None, func, *args)


def _to_bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _connect_ssh(
    hostname: str,
    port: int,
    username: str,
    timeout: float,
    key_path: Optional[str],
    key_passphrase: Optional[str],
    password: Optional[str],
) -> paramiko.SSHClient:
    """handles the logic of creating and configuring a paramiko ssh client."""
    ssh_client = paramiko.SSHClient()
    auto_add_host_key = _to_bool(os.getenv("SSH_AUTO_ADD_HOST_KEY"), default=False)
    if auto_add_host_key:
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    else:
        ssh_client.load_system_host_keys()
        ssh_client.set_missing_host_key_policy(paramiko.RejectPolicy())

    connect_kwargs = {
        "hostname": hostname,
        "username": username,
        "port": port,
        "timeout": timeout,
        "look_for_keys": False,
        "allow_agent": False,
    }

    if key_path:
        connect_kwargs["key_filename"] = key_path
        if key_passphrase:
            connect_kwargs["passphrase"] = key_passphrase
    elif password:
        connect_kwargs["password"] = password
    else:
        raise RuntimeError("missing REMOTE_SSH_KEY_PATH or REMOTE_SSH_PASSWORD for ssh authentication.")

    ssh_client.connect(**connect_kwargs)
    return ssh_client


@router.websocket("/ws/terminal")
async def websocket_terminal(websocket: WebSocket):
    """websocket endpoint for an interactive remote ssh terminal."""
    await websocket.accept()
    user = None
    hostname = None
    ssh_username = None
    ssh_port = int(os.getenv("REMOTE_SSH_PORT", "22"))
    ssh_client = None
    channel = None
    try:
        # first message must be an auth payload with token, cols, and rows
        auth_payload = await asyncio.wait_for(websocket.receive_json(), timeout=10)
        if auth_payload.get("type") != "auth":
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="missing auth payload")
            return

        token = auth_payload.get("token")
        cols = int(auth_payload.get("cols", 80))
        rows = int(auth_payload.get("rows", 24))

        user = await get_current_user_from_websocket(token)
        if user is None:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="unauthorized")
            return

        ssh_username = os.getenv("REMOTE_SSH_USERNAME")
        ssh_key_path = os.getenv("REMOTE_SSH_KEY_PATH")
        ssh_key_passphrase = os.getenv("REMOTE_SSH_KEY_PASSPHRASE")
        ssh_password = os.getenv("REMOTE_SSH_PASSWORD")

        private_host = os.getenv("REMOTE_SSH_PRIVATE_HOST")
        public_host = os.getenv("REMOTE_SSH_PUBLIC_HOST")
        private_timeout = float(os.getenv("REMOTE_SSH_CONNECT_TIMEOUT_PRIVATE", "2"))
        public_timeout = float(os.getenv("REMOTE_SSH_CONNECT_TIMEOUT_PUBLIC", "5"))

        if not ssh_username or not private_host:
            await websocket.close(
                code=status.WS_1011_INTERNAL_ERROR,
                reason="missing ssh target/identity configuration",
            )
            return

        if not ssh_key_path and not ssh_password:
            await websocket.close(
                code=status.WS_1011_INTERNAL_ERROR,
                reason="missing ssh authentication material for this user level",
            )
            return

        # ssh connection with automatic fallback: private -> public
        last_error: Optional[str] = None
        connection_attempts = [(private_host, private_timeout)]
        if public_host and public_host != private_host:
            connection_attempts.append((public_host, public_timeout))

        for candidate_host, candidate_timeout in connection_attempts:
            try:
                ssh_client = await run_in_thread(
                    _connect_ssh,
                    candidate_host,
                    ssh_port,
                    ssh_username,
                    candidate_timeout,
                    ssh_key_path,
                    ssh_key_passphrase,
                    ssh_password,
                )
                hostname = candidate_host
                break
            except Exception as exc:
                last_error = str(exc)
                log.warning(
                    f"ssh connect failed for {ssh_username}@{candidate_host}:{ssh_port}: {exc}"
                )

        if not ssh_client:
            log.error(
                f"all ssh connection attempts failed for {ssh_username}. last error: {last_error}"
            )
            await websocket.send_text("ssh connection failed on private/public routes.\r\n")
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
            return

        log.info(
            f"ssh websocket authenticated for user: {user.username} to {ssh_username}@{hostname}:{ssh_port}"
        )

        # open ssh channel and request pty
        channel = await run_in_thread(
            ssh_client.invoke_shell, term="xterm-256color", width=cols, height=rows
        )
        channel.setblocking(False)

        await websocket.send_text(f"successfully connected to {ssh_username}@{hostname}:{ssh_port}\r\n")

        # bidirectional bridge between websocket and ssh channel
        async def read_from_ssh_and_send_to_ws():
            while not channel.closed:
                try:
                    if channel.recv_ready():
                        data = await run_in_thread(channel.recv, 1024)
                        if data:
                            await websocket.send_bytes(data)
                    await asyncio.sleep(0.01)
                except Exception as e:
                    log.error(f"error reading from ssh or sending to ws: {e}")
                    break

        async def read_from_ws_and_send_to_ssh() -> None:
            while not channel.closed:
                try:
                    message = await websocket.receive_json()
                    message_type = message.get("type")
                    if message_type == "input":
                        data = message.get("data", "")
                        if data:
                            await run_in_thread(channel.send, data)
                    elif message_type == "resize":
                        cols = int(message.get("cols", 80))
                        rows = int(message.get("rows", 24))
                        await run_in_thread(channel.resize_pty, width=cols, height=rows)
                except WebSocketDisconnect:
                    break
                except Exception as e:
                    log.error(f"error reading from ws or sending to ssh: {e}")
                    break

        read_task = asyncio.create_task(read_from_ssh_and_send_to_ws())
        write_task = asyncio.create_task(read_from_ws_and_send_to_ssh())

        await asyncio.gather(read_task, write_task)

    except paramiko.AuthenticationException:
        log.warning(f"ssh authentication failed for {ssh_username}@{hostname}:{ssh_port}")
        await websocket.send_text("ssh authentication failed.\r\n")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
    except paramiko.SSHException as e:
        log.error(f"could not establish ssh connection to {hostname}:{ssh_port}: {e}")
        await websocket.send_text("could not establish ssh connection.\r\n")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
    except TimeoutError:
        log.error(f"ssh connection to {hostname}:{ssh_port} timed out.")
        await websocket.send_text("ssh connection timed out.\r\n")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
    except WebSocketDisconnect:
        username = user.username if user else "unknown"
        target = f"{ssh_username}@{hostname}:{ssh_port}" if hostname and ssh_username else "unknown"
        log.info(f"websocket disconnected for user {username} to {target}")
    except Exception as e:
        username = user.username if user else "unknown"
        target = f"{ssh_username}@{hostname}:{ssh_port}" if hostname and ssh_username else "unknown"
        log.error(f"unhandled error in ssh websocket for user {username} to {target}: {e}")
        await websocket.send_text("an unexpected server error occurred.\r\n")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
    finally:
        if channel and not channel.closed:
            await run_in_thread(channel.close)
        if ssh_client:
            await run_in_thread(ssh_client.close)
            if user and hostname and ssh_username:
                log.info(f"ssh client closed for user {user.username} to {hostname}:{ssh_port}")