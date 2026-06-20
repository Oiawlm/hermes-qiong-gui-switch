# Hermes 穷鬼 Switch 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 一个 CLI 菜单工具，让用户一键切换 Hermes 的主模型和视觉模型供应商，支持跨供应商混搭，自动处理 base64/url 图片模式差异。

**Architecture:** 单文件 Python CLI + providers.yaml 配置文件 + 内嵌 Agnes 代理。读配置 → 显示菜单 → 用户选择 → 写 Hermes config.yaml → 提示重启。

**Tech Stack:** Python 3.11+ 标准库（argparse, http.server, json, subprocess, urllib）+ PyYAML

**仓库:** Oiawlm/hermes-qiong-gui-switch（公开，MIT）

---

## 文件结构

```
hermes-qiong-gui-switch/
  providers.yaml          # 用户填的供应商配置（含示例）
  hermes_qiong_gui_switch/
    __init__.py
    switcher.py           # 主菜单 + config 读写
    proxy.py              # 内嵌 Agnes base64→URL 代理
    models.py             # 模型能力标记 + 自动检测
  README.md               # 安装和使用说明
  .gitignore              # 忽略 providers.yaml（含 key）
```

---

### Task 1: 项目骨架 + providers.yaml 示例

**Files:**
- Create: `hermes-qiong-gui-switch/providers.yaml.example`
- Create: `hermes-qiong-gui-switch/hermes_qiong_gui_switch/__init__.py`
- Create: `hermes-qiong-gui-switch/.gitignore`
- Create: `hermes-qiong-gui-switch/README.md`

- [ ] **Step 1: 创建 providers.yaml.example**

```yaml
# Hermes 穷鬼 Switch - 供应商配置
# 复制此文件为 providers.yaml，填入你的 API key
# providers.yaml 已在 .gitignore 中，不会被提交

providers:
  火山方舟-AgentPlan:
    base_url: https://ark.cn-beijing.volces.com/api/plan/v3
    api_key: 你的key
    models:
      - deepseek-v4-pro
      - doubao-seed-2.0-pro

  火山方舟-按量:
    base_url: https://ark.cn-beijing.volces.com/api/plan/v3
    api_key: 你的key
    models:
      - deepseek-v4-pro
      - doubao-seed-2.0-pro

  DeepSeek官方:
    base_url: https://api.deepseek.com
    api_key: 你的key
    models:
      - deepseek-v4-pro

  智谱:
    base_url: https://open.bigmodel.cn/api/paas/v4
    api_key: 你的key
    models:
      - glm-4.5-air
      - glm-4.1v-flashx

  Agnes免费:
    base_url: http://localhost:8899
    api_key: 你的Agnes key
    models:
      - agnes-2.0-flash
```

- [ ] **Step 2: 创建 .gitignore**

```
providers.yaml
__pycache__/
*.pyc
```

- [ ] **Step 3: 创建空的 __init__.py**

```python
"""Hermes 穷鬼 Switch - 一键切换 Hermes 模型供应商"""
```

- [ ] **Step 4: 创建 README.md 骨架**

```markdown
# Hermes 穷鬼 Switch

一键切换 Hermes Agent 的主模型和视觉模型供应商。穷鬼专用。

## 安装

```bash
git clone https://github.com/Oiawlm/hermes-qiong-gui-switch.git
cd hermes-qiong-gui-switch
cp providers.yaml.example providers.yaml
# 编辑 providers.yaml，填入你的 API key
```

## 使用

```bash
python -m hermes_qiong_gui_switch.switcher
```

上下键选模型，回车确认，一键写入 Hermes 配置。
切换后需重启 Hermes 终端。
```

- [ ] **Step 5: 验证文件结构**

Run: `ls -la hermes-qiong-gui-switch/`

- [ ] **Step 6: Commit**

```bash
cd hermes-qiong-gui-switch
git init
git add .
git commit -m "init: 项目骨架 + providers.yaml 示例"
```

---

### Task 2: 模型能力标记模块

**Files:**
- Create: `hermes-qiong-gui-switch/hermes_qiong_gui_switch/models.py`

- [ ] **Step 1: 创建 models.py**

```python
"""模型能力标记 — 穷鬼 Switch 内置的模型知识库"""

# 已知模型的能力标记
# type: "text" = 纯文本, "vision" = 纯视觉, "multimodal" = 多模态（既能当主模型也能当视觉模型）
# image_mode: "base64" = 原生支持 base64, "url" = 需要代理转 URL
KNOWN_MODELS = {
    "deepseek-v4-pro": {"type": "text", "image_mode": None},
    "deepseek-v4-flash": {"type": "text", "image_mode": None},
    "doubao-seed-2.0-pro": {"type": "multimodal", "image_mode": "base64"},
    "doubao-seed-2.0-lite": {"type": "multimodal", "image_mode": "base64"},
    "glm-4.5-air": {"type": "text", "image_mode": None},
    "glm-4.7": {"type": "text", "image_mode": None},
    "glm-4.1v-flashx": {"type": "vision", "image_mode": "base64"},
    "glm-4.6v": {"type": "vision", "image_mode": "base64"},
    "agnes-2.0-flash": {"type": "vision", "image_mode": "url"},
}


def get_model_info(model_name: str) -> dict:
    """获取模型能力信息，未知模型默认纯文本+base64"""
    model_lower = model_name.lower()
    
    # 先查已知列表
    if model_name in KNOWN_MODELS:
        return KNOWN_MODELS[model_name]
    
    # 自动推断
    info = {"type": "text", "image_mode": "base64"}
    
    if "agnes" in model_lower:
        info["image_mode"] = "url"
    if any(kw in model_lower for kw in ["vision", "vl", "vl2", "-v"]):
        info["type"] = "vision"
    if any(kw in model_lower for kw in ["doubao", "seed", "gemini", "gpt-4o", "claude"]):
        info["type"] = "multimodal"
    
    return info


def get_models_for_slot(providers: dict, slot: str) -> list:
    """返回可用于某个槽位的模型列表
    
    slot: "main" = 主模型（text + multimodal）
          "vision" = 视觉模型（vision + multimodal）
    
    返回: [(provider_name, model_name, model_info), ...]
    """
    results = []
    for pname, pconfig in providers.items():
        for model_name in pconfig.get("models", []):
            info = get_model_info(model_name)
            if slot == "main" and info["type"] in ("text", "multimodal"):
                results.append((pname, model_name, info))
            elif slot == "vision" and info["type"] in ("vision", "multimodal"):
                results.append((pname, model_name, info))
    return results
```

- [ ] **Step 2: 验证模型查询**

Run: `cd hermes-qiong-gui-switch && python -c "from hermes_qiong_gui_switch.models import get_model_info, get_models_for_slot; print(get_model_info('doubao-seed-2.0-pro')); print(get_model_info('glm-4.5-air'))"`

Expected: `{'type': 'multimodal', 'image_mode': 'base64'}` 和 `{'type': 'text', 'image_mode': None}`

- [ ] **Step 3: Commit**

```bash
git add hermes_qiong_gui_switch/models.py
git commit -m "feat: 模型能力标记模块"
```

---

### Task 3: 内嵌 Agnes 代理

**Files:**
- Create: `hermes-qiong-gui-switch/hermes_qiong_gui_switch/proxy.py`

- [ ] **Step 1: 创建 proxy.py**

```python
"""内嵌 Agnes 视觉代理 — 自动将 base64 图片上传 0x0.st 换 URL 后转发 Agnes"""

import json
import base64
import tempfile
import subprocess
import sys
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

AGNES_API = "https://apihub.agnes-ai.com/v1"
UPLOAD_URL = "https://0x0.st"
DEFAULT_PORT = 8899


class ProxyHandler(BaseHTTPRequestHandler):
    agnes_key = ""

    def do_POST(self):
        if self.path != "/v1/chat/completions":
            self.send_error(404)
            return

        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        data = json.loads(body)

        messages = data.get("messages", [])
        self._convert_base64_images(messages)

        modified_body = json.dumps(data).encode("utf-8")
        req = Request(
            f"{AGNES_API}/chat/completions",
            data=modified_body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.agnes_key}",
            },
        )

        try:
            with urlopen(req, timeout=120) as resp:
                self.send_response(resp.status)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(resp.read())
        except HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            self.send_response(e.code)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(err_body.encode())
        except URLError as e:
            self.send_error(502, f"上游不可达: {e}")

    def _convert_base64_images(self, messages):
        """把 base64 图片上传 0x0.st，替换为公网 URL"""
        for msg in messages:
            content = msg.get("content")
            if not isinstance(content, list):
                continue
            for part in content:
                if part.get("type") != "image_url":
                    continue
                image_url = part.get("image_url", {})
                url = image_url.get("url", "")
                if not url.startswith("data:image/"):
                    continue

                # 提取 base64 数据
                header, b64data = url.split(",", 1)
                img_bytes = base64.b64decode(b64data)

                # 写入临时文件
                ext = header.split("/")[1].split(";")[0]
                with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as f:
                    f.write(img_bytes)
                    tmp_path = f.name

                # 上传到 0x0.st
                try:
                    result = subprocess.run(
                        ["curl", "-s", "-F", f"file=@{tmp_path}", UPLOAD_URL],
                        capture_output=True, text=True, timeout=30
                    )
                    public_url = result.stdout.strip()
                    if public_url.startswith("http"):
                        image_url["url"] = public_url
                except Exception:
                    pass
                finally:
                    os.unlink(tmp_path)

    def do_GET(self):
        if self.path == "/v1/models":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "object": "list",
                "data": [{"id": "agnes-2.0-flash", "object": "model", "owned_by": "agnes"}]
            }).encode())
        else:
            self.send_error(404)

    def log_message(self, fmt, *args):
        pass  # 静默


def start_proxy(agnes_api_key: str, port: int = DEFAULT_PORT) -> threading.Thread:
    """启动代理，返回线程对象"""
    ProxyHandler.agnes_key = agnes_api_key
    server = HTTPServer(("127.0.0.1", port), ProxyHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return thread


def is_proxy_running(port: int = DEFAULT_PORT) -> bool:
    """检查代理是否已在运行"""
    try:
        from urllib.request import urlopen
        with urlopen(f"http://127.0.0.1:{port}/v1/models", timeout=2) as resp:
            return resp.status == 200
    except Exception:
        return False
```

- [ ] **Step 2: 验证代理能启动**

Run: `cd hermes-qiong-gui-switch && python -c "from hermes_qiong_gui_switch.proxy import is_proxy_running; print('running:', is_proxy_running())"`

Expected: `running: False`（当前没跑）

- [ ] **Step 3: Commit**

```bash
git add hermes_qiong_gui_switch/proxy.py
git commit -m "feat: 内嵌 Agnes base64→URL 代理"
```

---

### Task 4: 主切换逻辑

**Files:**
- Create: `hermes-qiong-gui-switch/hermes_qiong_gui_switch/switcher.py`

- [ ] **Step 1: 创建 switcher.py**

```python
"""Hermes 穷鬼 Switch — 主程序"""

import os
import sys
import yaml
from pathlib import Path

from .models import get_model_info, get_models_for_slot
from .proxy import start_proxy, is_proxy_running

HERMES_CONFIG = Path(os.environ.get("LOCALAPPDATA", "")) / "hermes" / "config.yaml"
PROVIDERS_FILE = Path(__file__).parent.parent / "providers.yaml"


def load_providers():
    """加载供应商配置"""
    if not PROVIDERS_FILE.exists():
        print(f"错误: 找不到 {PROVIDERS_FILE}")
        print("请复制 providers.yaml.example 为 providers.yaml 并填入你的 API key")
        sys.exit(1)
    with open(PROVIDERS_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_current_config():
    """读取当前 Hermes 配置"""
    if not HERMES_CONFIG.exists():
        return None, None
    with open(HERMES_CONFIG, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    main_model = cfg.get("model", {}).get("default", "未知")
    vision_model = cfg.get("auxiliary", {}).get("vision", {}).get("model", "未知")
    return main_model, vision_model


def write_hermes_config(providers, main_choice, vision_choice):
    """写入 Hermes config.yaml"""
    # 读取当前配置
    with open(HERMES_CONFIG, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    # 主模型
    if main_choice:
        pname, mname = main_choice
        pconfig = providers["providers"][pname]
        cfg["model"]["default"] = mname
        cfg["model"]["provider"] = "custom"
        cfg["model"]["base_url"] = pconfig["base_url"]
        cfg["model"]["api_key"] = pconfig["api_key"]

    # 视觉模型
    if vision_choice:
        pname, mname = vision_choice
        pconfig = providers["providers"][pname]
        info = get_model_info(mname)
        
        cfg["auxiliary"]["vision"]["model"] = mname
        cfg["auxiliary"]["vision"]["provider"] = "main"
        cfg["auxiliary"]["vision"]["api_key"] = pconfig["api_key"]
        
        if info["image_mode"] == "url":
            # Agnes 模式：走本地代理
            cfg["auxiliary"]["vision"]["base_url"] = "http://localhost:8899/v1"
        else:
            # 直连模式
            cfg["auxiliary"]["vision"]["base_url"] = pconfig["base_url"]

    # 写回
    with open(HERMES_CONFIG, "w", encoding="utf-8") as f:
        yaml.dump(cfg, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


def show_menu(providers):
    """显示 CLI 菜单"""
    main_models = get_models_for_slot(providers["providers"], "main")
    vision_models = get_models_for_slot(providers["providers"], "vision")

    current_main, current_vision = load_current_config()

    main_choice = None
    vision_choice = None

    while True:
        print("\n" + "=" * 50)
        print("  Hermes 穷鬼 Switch")
        print("=" * 50)
        print(f"  当前: 主模型 {current_main} | 视觉 {current_vision}")
        print()

        print("  主模型:")
        for i, (pname, mname, info) in enumerate(main_models, 1):
            marker = " ←" if main_choice and main_choice == (pname, mname) else ""
            print(f"    {i}. {mname} ({pname}){marker}")

        print()
        print("  视觉模型:")
        for j, (pname, mname, info) in enumerate(vision_models, len(main_models) + 1):
            marker = " ←" if vision_choice and vision_choice == (pname, mname) else ""
            print(f"    {j}. {mname} ({pname}){marker}")

        print()
        print("  A. 应用配置并退出")
        print("  Q. 退出（不保存）")
        print()

        choice = input("  选择: ").strip().upper()

        if choice == "Q":
            print("已取消。")
            sys.exit(0)

        if choice == "A":
            if not main_choice and not vision_choice:
                print("请至少选择一个模型。")
                continue
            break

        try:
            idx = int(choice) - 1
            if idx < len(main_models):
                main_choice = main_models[idx][:2]
                print(f"主模型 → {main_choice[1]}")
            elif idx < len(main_models) + len(vision_models):
                vision_choice = vision_models[idx - len(main_models)][:2]
                print(f"视觉模型 → {vision_choice[1]}")
            else:
                print("无效选择。")
        except (ValueError, IndexError):
            print("无效选择。")

    return main_choice, vision_choice


def main():
    providers = load_providers()
    main_choice, vision_choice = show_menu(providers)

    # 如果选了 Agnes 视觉模型，确保代理在跑
    if vision_choice:
        _, mname = vision_choice
        info = get_model_info(mname)
        if info["image_mode"] == "url":
            if not is_proxy_running():
                print("启动 Agnes 代理...")
                pconfig = providers["providers"][vision_choice[0]]
                start_proxy(pconfig["api_key"])
                import time
                time.sleep(1)
                if is_proxy_running():
                    print("代理已启动 (localhost:8899)")
                else:
                    print("警告: 代理启动失败，视觉功能可能不可用")

    write_hermes_config(providers, main_choice, vision_choice)
    print("\n配置已写入 Hermes config.yaml")
    print("请重启 Hermes 终端使配置生效。")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 测试菜单显示**

Run: `cd hermes-qiong-gui-switch && cp providers.yaml.example providers.yaml && python -m hermes_qiong_gui_switch.switcher`

Expected: 显示菜单，列出所有模型，按 Q 退出。

- [ ] **Step 3: 测试配置写入**

手动选一个主模型和视觉模型，按 A 应用。然后检查 config.yaml。

Run: `grep -A3 "default:" "$LOCALAPPDATA/hermes/config.yaml" && grep -A6 "vision:" "$LOCALAPPDATA/hermes/config.yaml"`

Expected: 模型名和 base_url 已更新。

- [ ] **Step 4: Commit**

```bash
git add hermes_qiong_gui_switch/switcher.py
git commit -m "feat: 主切换逻辑 — CLI 菜单 + config 写入"
```

---

### Task 5: README 完善 + 发布

**Files:**
- Modify: `hermes-qiong-gui-switch/README.md`

- [ ] **Step 1: 完善 README.md**

```markdown
# Hermes 穷鬼 Switch

一键切换 Hermes Agent 的主模型和视觉模型供应商。穷鬼专用。

## 功能

- 独立选择主模型和视觉模型，跨供应商混搭
- 自动处理 base64/URL 图片模式差异
- 选 Agnes 免费模型时自动启动本地代理
- 一键写入 Hermes config.yaml

## 安装

```bash
git clone https://github.com/Oiawlm/hermes-qiong-gui-switch.git
cd hermes-qiong-gui-switch
cp providers.yaml.example providers.yaml
```

编辑 `providers.yaml`，填入你的 API key。

## 使用

```bash
python -m hermes_qiong_gui_switch.switcher
```

1. 输入数字选择主模型
2. 输入数字选择视觉模型（可选）
3. 按 A 应用配置
4. 重启 Hermes 终端

## 供应商配置

在 `providers.yaml` 中添加你的供应商：

```yaml
providers:
  我的供应商:
    base_url: https://api.example.com/v1
    api_key: sk-xxx
    models:
      - model-name-1
      - model-name-2
```

工具会自动识别模型能力（纯文本/多模态/视觉）和图片模式（base64/URL）。

## 注意事项

- `providers.yaml` 包含 API key，已在 .gitignore 中，不会被提交
- 切换后需重启 Hermes 终端
- Agnes 模型需要本地代理（工具自动启动）

## 许可证

MIT
```

- [ ] **Step 2: 最终验证**

Run: `cd hermes-qiong-gui-switch && python -m hermes_qiong_gui_switch.switcher`

完整走一遍流程：选模型 → 应用 → 检查 config.yaml。

- [ ] **Step 3: 推送到 GitHub**

```bash
cd hermes-qiong-gui-switch
git add README.md
git commit -m "docs: 完善 README"
git remote add origin https://github.com/Oiawlm/hermes-qiong-gui-switch.git
git push -u origin main
```

---

## 自检

1. Spec 覆盖：主模型选择 ✓ 视觉模型选择 ✓ 跨供应商混搭 ✓ 代理集成 ✓ 自动检测图片模式 ✓ config 写入 ✓
2. 无占位符：所有代码都是完整可运行的
3. 类型一致：`get_model_info` 返回 dict，`get_models_for_slot` 返回 list of tuples，switcher 消费一致
