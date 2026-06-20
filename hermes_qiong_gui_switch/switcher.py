"""Hermes 穷鬼 Switch — 主程序 CLI 菜单 + config 写入"""

import os
import re
import subprocess
import sys
import yaml
from pathlib import Path

from .models import BUILTIN_PROVIDERS, get_model_info, get_models_for_slot
from .proxy import start_proxy_process, is_proxy_running

def _fallback_hermes_config_path() -> Path:
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / "hermes" / "config.yaml"
    return Path.home() / ".hermes" / "config.yaml"


def resolve_hermes_config_path() -> Path:
    """Return the config path reported by the active `hermes` executable."""
    try:
        result = subprocess.run(
            ["hermes", "config"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return _fallback_hermes_config_path()

    output = f"{result.stdout}\n{result.stderr}"
    match = re.search(r"Config:\s*(.+?config\.ya?ml)", output, re.IGNORECASE)
    if match:
        return Path(match.group(1).strip())
    return _fallback_hermes_config_path()


HERMES_CONFIG = _fallback_hermes_config_path()
PROJECT_ROOT = Path(__file__).parent.parent
PROVIDERS_FILE = PROJECT_ROOT / "providers.yaml"
LOCAL_PROVIDERS_FILE = PROJECT_ROOT / "providers.local.yaml"


def load_providers() -> dict:
    """加载供应商配置：内置 base_url + 模型 + 用户填的 API key。"""
    providers_file = LOCAL_PROVIDERS_FILE if LOCAL_PROVIDERS_FILE.exists() else PROVIDERS_FILE
    if not providers_file.exists():
        print(f"错误: 找不到 {PROVIDERS_FILE}")
        print("请创建 providers.yaml 并填入你的 API key")
        sys.exit(1)

    user_keys = {}
    with open(providers_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                name, key = line.split("=", 1)
                user_keys[name.strip()] = key.strip()

    providers = {}
    for name, builtin in BUILTIN_PROVIDERS.items():
        key = user_keys.get(name, "").strip()
        if not key or key == "你的key":
            continue
        providers[name] = {
            "base_url": builtin["base_url"],
            "api_key": key,
            "models": builtin["models"],
        }

    if not providers:
        print("错误: providers.yaml 中没有有效的 API key")
        print("请编辑 providers.yaml，至少填入一个供应商的 key")
        sys.exit(1)

    return providers


def build_slot_notice(providers: dict) -> str:
    """说明只会出现在第二步的视觉模型，避免用户误以为配置没读到。"""
    main_pairs = {
        (pname, model_name)
        for pname, model_name, _info in get_models_for_slot(providers, "main")
    }
    vision_only = [
        (pname, model_name)
        for pname, model_name, _info in get_models_for_slot(providers, "vision")
        if (pname, model_name) not in main_pairs
    ]
    if not vision_only:
        return ""

    lines = ["  提示：第一步只选主模型；下面这些视觉模型只会在第二步出现："]
    for pname, model_name in vision_only:
        lines.append(f"  - {model_name}（{pname}）")
    return "\n".join(lines)


def load_current_config(config_path: Path | str | None = None) -> tuple:
    """读取当前 Hermes 主模型和视觉模型名称"""
    path = Path(config_path) if config_path is not None else resolve_hermes_config_path()
    if not path.exists():
        return "未知", "未知"
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    main_model = cfg.get("model", {}).get("default", "未知")
    vision_model = cfg.get("auxiliary", {}).get("vision", {}).get("model", "未知")
    return main_model, vision_model


def write_hermes_config(
    providers: dict,
    main_choice,
    vision_choice,
    config_path: Path | str | None = None,
) -> None:
    """将用户选择的模型写入 Hermes config.yaml"""
    path = Path(config_path) if config_path is not None else resolve_hermes_config_path()
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
    else:
        cfg = {}

    cfg.setdefault("model", {})
    cfg.setdefault("auxiliary", {}).setdefault("vision", {})

    if main_choice is not None:
        pname, mname = main_choice
        pconfig = providers[pname]
        cfg["model"]["default"] = mname
        cfg["model"]["provider"] = "custom"
        cfg["model"]["base_url"] = pconfig["base_url"]
        cfg["model"]["api_key"] = pconfig["api_key"]

    if vision_choice is not None:
        pname, mname = vision_choice
        pconfig = providers[pname]
        info = get_model_info(mname)
        cfg["auxiliary"]["vision"]["model"] = mname
        cfg["auxiliary"]["vision"]["provider"] = "custom"
        cfg["auxiliary"]["vision"]["api_key"] = pconfig["api_key"]
        if info["image_mode"] == "url":
            cfg["auxiliary"]["vision"]["base_url"] = "http://localhost:8899/v1"
        else:
            cfg["auxiliary"]["vision"]["base_url"] = pconfig["base_url"]

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(cfg, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


def pick_one(title, models, current_name):
    """问用户选一个，返回 (provider_name, model_name) 或 None"""
    print()
    print(f"  {title}")
    print(f"  当前用的是: {current_name}")
    print()
    for i, (pname, mname, _info) in enumerate(models, 1):
        print(f"  {i}. {mname}（{pname}）")
    print(f"  回车 = 不换，保持当前")
    print()

    while True:
        choice = input("  输入数字: ").strip()
        if choice == "":
            return None
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(models):
                return (models[idx][0], models[idx][1])
        except ValueError:
            pass
        print(f"  请输入 1 到 {len(models)}，或直接回车跳过")


def main() -> None:
    providers = load_providers()
    config_path = resolve_hermes_config_path()
    main_models = get_models_for_slot(providers, "main")
    vision_models = get_models_for_slot(providers, "vision")
    current_main, current_vision = load_current_config(config_path)

    print()
    print("=" * 50)
    print("  Hermes 穷鬼 Switch")
    print("=" * 50)
    print(f"  Hermes config: {config_path}")
    notice = build_slot_notice(providers)
    if notice:
        print()
        print(notice)

    # 第一步：选主模型
    main_choice = pick_one("第一步：选主模型", main_models, current_main)

    # 第二步：选视觉模型
    vision_choice = pick_one("第二步：选视觉模型（可跳过）", vision_models, current_vision)

    # 确认
    print()
    if main_choice:
        print(f"  主模型 → {main_choice[1]}")
    else:
        print(f"  主模型 → 不换（保持 {current_main}）")
    if vision_choice:
        print(f"  视觉模型 → {vision_choice[1]}")
    else:
        print(f"  视觉模型 → 不换（保持 {current_vision}）")

    confirm = input("\n  确认应用？(y/n): ").strip().lower()
    if confirm not in ("y", "yes", ""):
        print("已取消。")
        sys.exit(0)

    # 如果选了 Agnes 视觉模型，启动代理
    if vision_choice is not None:
        _pname, mname = vision_choice
        info = get_model_info(mname)
        if info["image_mode"] == "url":
            if not is_proxy_running():
                print("启动 Agnes 代理...")
                pconfig = providers[vision_choice[0]]
                start_proxy_process(pconfig["api_key"])
                import time
                time.sleep(1)
                if is_proxy_running():
                    print("代理已启动 (localhost:8899)")
                else:
                    print("警告: 代理启动失败")

    write_hermes_config(providers, main_choice, vision_choice, config_path=config_path)
    print(f"\n搞定！已写入 {config_path}")
    print("重启 Hermes 终端就行了。")


if __name__ == "__main__":
    main()
