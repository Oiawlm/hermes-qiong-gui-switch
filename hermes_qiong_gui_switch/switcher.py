"""Hermes 穷鬼 Switch — 主程序 CLI 菜单 + config 写入"""

import os
import sys
import yaml
from pathlib import Path

from .models import BUILTIN_PROVIDERS, get_model_info, get_models_for_slot
from .proxy import start_proxy, is_proxy_running

HERMES_CONFIG = Path(os.environ["LOCALAPPDATA"]) / "hermes" / "config.yaml"
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


def load_current_config() -> tuple:
    """读取当前 Hermes 主模型和视觉模型名称"""
    if not HERMES_CONFIG.exists():
        return "未知", "未知"
    with open(HERMES_CONFIG, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    main_model = cfg.get("model", {}).get("default", "未知")
    vision_model = cfg.get("auxiliary", {}).get("vision", {}).get("model", "未知")
    return main_model, vision_model


def write_hermes_config(providers: dict, main_choice, vision_choice) -> None:
    """将用户选择的模型写入 Hermes config.yaml"""
    with open(HERMES_CONFIG, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

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
        cfg["auxiliary"]["vision"]["provider"] = "main"
        cfg["auxiliary"]["vision"]["api_key"] = pconfig["api_key"]
        if info["image_mode"] == "url":
            cfg["auxiliary"]["vision"]["base_url"] = "http://localhost:8899/v1"
        else:
            cfg["auxiliary"]["vision"]["base_url"] = pconfig["base_url"]

    with open(HERMES_CONFIG, "w", encoding="utf-8") as f:
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
    main_models = get_models_for_slot(providers, "main")
    vision_models = get_models_for_slot(providers, "vision")
    current_main, current_vision = load_current_config()

    print()
    print("=" * 50)
    print("  Hermes 穷鬼 Switch")
    print("=" * 50)

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
                start_proxy(pconfig["api_key"])
                import time
                time.sleep(1)
                if is_proxy_running():
                    print("代理已启动 (localhost:8899)")
                else:
                    print("警告: 代理启动失败")

    write_hermes_config(providers, main_choice, vision_choice)
    print("\n搞定！重启 Hermes 终端就行了。")


if __name__ == "__main__":
    main()
