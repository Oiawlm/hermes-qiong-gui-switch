"""内嵌 HTTP 代理 — 将 base64 图片转为公开 URL 后转发给 Agnes API。

Agnes API 只接受图片 URL，不接受 base64 data URI。
本代理在本地启动一个 HTTP 服务，拦截 /v1/chat/completions 请求，
将其中的 base64 图片上传到 0x0.st 获得公开 URL，再转发给真正的 Agnes API。
"""

import base64
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import urllib.request
import urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler

AGNES_API = "https://apihub.agnes-ai.com/v1"
UPLOAD_URL = "https://0x0.st"
DEFAULT_PORT = 8899

# ---------------------------------------------------------------------------
# 匹配 data:image/...;base64,... 格式的 data URI
_DATA_URI_RE = re.compile(
    r"^data:image/(?P<ext>[a-zA-Z0-9.+-]+);base64,(?P<data>.+)$"
)


def _upload_to_0x0st(filepath: str) -> str | None:
    """将本地文件上传到 0x0.st，返回公开 URL。

    使用 curl -s -F "file=@<filepath>" <UPLOAD_URL>。
    0x0.st 返回的是纯文本 URL（以 https://0x0.st/ 开头）。
    """
    try:
        result = subprocess.run(
            ["curl", "-s", "-F", f"file=@{filepath}", UPLOAD_URL],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            return None
        url = result.stdout.strip()
        if url.startswith("https://0x0.st/"):
            return url
        return None
    except Exception:
        return None


# ---------------------------------------------------------------------------
class ProxyHandler(BaseHTTPRequestHandler):
    """HTTP 代理处理器 — 拦截 OpenAI 兼容端点并转发到 Agnes API。"""

    agnes_key: str = ""

    # ---- helpers -----------------------------------------------------------

    @classmethod
    def _convert_base64_images(cls, messages: list) -> list:
        """遍历 messages，将 image_url 中的 base64 data URI 替换为公开 URL。

        只处理 content 为数组格式的消息（多模态消息）。
        对每个 image_url 部分，如果 url 以 data:image/ 开头，
        则解码 base64 写入临时文件，上传到 0x0.st，替换为公开 URL。

        Args:
            messages: OpenAI 格式的 messages 列表。

        Returns:
            处理后的 messages 列表（原地修改）。
        """
        for message in messages:
            content = message.get("content")
            if not isinstance(content, list):
                continue
            for part in content:
                if not isinstance(part, dict):
                    continue
                image_url = part.get("image_url")
                if not isinstance(image_url, dict):
                    continue
                url = image_url.get("url", "")
                match = _DATA_URI_RE.match(url)
                if not match:
                    continue

                ext = match.group("ext")
                if ext == "jpeg":
                    ext = "jpg"  # 规范化扩展名
                b64_data = match.group("data")

                try:
                    raw = base64.b64decode(b64_data)
                except Exception:
                    continue

                # 写入临时文件
                suffix = f".{ext}" if ext else ".png"
                with tempfile.NamedTemporaryFile(
                    suffix=suffix, delete=False
                ) as tmp:
                    tmp.write(raw)
                    tmp_path = tmp.name

                # 上传
                public_url = _upload_to_0x0st(tmp_path)

                # 清理临时文件
                try:
                    import os
                    os.unlink(tmp_path)
                except Exception:
                    pass

                if public_url:
                    image_url["url"] = public_url

        return messages

    # ---- HTTP methods ------------------------------------------------------

    def do_POST(self) -> None:
        """处理 POST 请求。目前只处理 /v1/chat/completions。"""
        if self.path != "/v1/chat/completions":
            self.send_error(404, "Not Found")
            return

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            self.send_error(400, "Bad Request: invalid JSON")
            return

        # 转换 base64 图片
        messages = payload.get("messages", [])
        payload["messages"] = self._convert_base64_images(messages)

        # 转发到 Agnes API
        forward_body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{AGNES_API}/chat/completions",
            data=forward_body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.agnes_key}",
            },
        )

        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                response_body = resp.read()
                self.send_response(resp.status)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(response_body)
        except urllib.error.HTTPError as e:
            error_body = e.read()
            self.send_response(e.code)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(error_body)
        except Exception:
            self.send_error(502, "Bad Gateway: failed to reach Agnes API")

    def do_GET(self) -> None:
        """处理 GET 请求。返回 /v1/models 模型列表。"""
        if self.path == "/v1/models":
            body = json.dumps({
                "object": "list",
                "data": [
                    {
                        "id": "agnes-2.0-flash",
                        "object": "model",
                        "owned_by": "agnes",
                    }
                ],
            }).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_error(404, "Not Found")

    def log_message(self, format, *args) -> None:
        """静默日志 — 不输出任何内容。"""
        pass


# ---------------------------------------------------------------------------
def start_proxy(agnes_api_key: str, port: int = DEFAULT_PORT) -> threading.Thread:
    """启动内嵌代理服务器。

    Args:
        agnes_api_key: Agnes API 密钥。
        port: 监听端口，默认 8899。

    Returns:
        运行代理服务器的 daemon 线程。
    """
    ProxyHandler.agnes_key = agnes_api_key
    server = HTTPServer(("127.0.0.1", port), ProxyHandler)

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return thread


def start_proxy_process(agnes_api_key: str, port: int = DEFAULT_PORT) -> subprocess.Popen:
    """Start the Agnes proxy as a background process that survives the switcher."""
    env = os.environ.copy()
    env["AGNES_API_KEY"] = agnes_api_key
    env["AGNES_PROXY_PORT"] = str(port)

    kwargs = {
        "env": env,
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
        "stdin": subprocess.DEVNULL,
    }
    if os.name == "nt":
        kwargs["creationflags"] = (
            getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
            | getattr(subprocess, "DETACHED_PROCESS", 0)
        )
    else:
        kwargs["start_new_session"] = True

    return subprocess.Popen(
        [sys.executable, "-m", "hermes_qiong_gui_switch.proxy"],
        **kwargs,
    )


def is_proxy_running(port: int = DEFAULT_PORT) -> bool:
    """检查代理服务器是否正在运行。

    Args:
        port: 代理端口，默认 8899。

    Returns:
        True 如果代理返回 200，否则 False。
    """
    try:
        req = urllib.request.Request(f"http://127.0.0.1:{port}/v1/models")
        with urllib.request.urlopen(req, timeout=2) as resp:
            return resp.status == 200
    except Exception:
        return False


def main() -> None:
    agnes_key = os.environ.get("AGNES_API_KEY", "").strip()
    if not agnes_key:
        raise SystemExit("AGNES_API_KEY is required")
    port = int(os.environ.get("AGNES_PROXY_PORT", str(DEFAULT_PORT)))
    ProxyHandler.agnes_key = agnes_key
    server = HTTPServer(("127.0.0.1", port), ProxyHandler)
    server.serve_forever()


if __name__ == "__main__":
    main()
