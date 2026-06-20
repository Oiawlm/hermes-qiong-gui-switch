"""Hermes 穷鬼 Switch — 主程序 CLI 菜单 + config 写入"""

import os
import sys
import yaml
from pathlib import Path

from .models import BUILTIN_PROVIDERS, get_model_info, get_models_for_slot
from .proxy import start_proxy, is_proxy_running

HERMES_CONFIG = Path(os.environ["LOCALAPPDATA"]) / "hermes" / "config.yaml"
PROVIDERS_FILE = Path(__file__).parent.parent / "providers.yaml"


def load_providers() -> dict:
    """加载供应商配置：内置 base_url + 模型 + 用户填的 API key。
    
    用户只需在 providers.yaml 里填 key，格式（等号格式，不是 YAML）：
        火山方舟-AgentPlan=sk-xxx
        DeepSeek官方=sk-xxx
    
    base_url 和模型列表全部内置，用户不用管。
    """
    if not PROVIDERS_FILE.exists():
        print(f"错误: 找不到 {PROVIDERS_FILE}")
        print("请创建 providers.yaml 并填入你的 API key")
        sys.exit(1)

    # 解析 key=value 格式（不是 YAML，就是纯文本）
    user_keys = {}
    with open(PROVIDERS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                name, key = line.split("=", 1)
                user_keys[name.strip()] = key.strip()

    # 合并：内置配置 + 用户 key，没有 key 的供应商跳过
    providers = {}
    for name, builtin in BUILTIN_PROVIDERS.items():
        key = user_keys.get(name, "").strip()
        if not key or key == "你的key":
            continue  # 用户没填 key，跳过这个供应商
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


def show_menu(providers: dict) -> tuple:
    """CLI 交互菜单"""
    main_models = get_models_for_slot(providers, "main")
    vision_models = get_models_for_slot(providers, "vision")
    current_main, current_vision = load_current_config()

    main_choice = None
    vision_choice = None

    while True:
        print("\n" + "=" * 50)
        print("  Hermes 穷鬼 Switch")
        print("=" * 50)
        print(f"  当前: 主模型 {current_main} | 视觉 {current_vision}")
        print()
        print("  --- 主模型（输数字选）---")
        for i, (pname, mname, _info) in enumerate(main_models, 1):
            marker = " ← 当前" if mname == current_main else ""
            print(f"  {i}. {mname} ({pname}){marker}")

        print()
        print("  --- 视觉模型（输数字选）---")
        offset = len(main_models)
        for j, (pname, mname, _info) in enumerate(vision_models, offset + 1):
            marker = " ← 当前" if mname == current_vision else ""
            print(f"  {j}. {mname} ({pname}){marker}")

        print()
        print("  选好后按 A 应用，按 Q 退出")
        print()

        choice = input("  输入数字或字母: ").strip().upper()

        if choice == "Q":
            print("已取消。")
            sys.exit(0)

        if choice == "A":
            if main_choice is None and vision_choice is None:
                print("请至少选择一个模型。")
                continue
            break

        try:
            idx = int(choice) - 1
            if idx < len(main_models):
                main_choice = (main_models[idx][0], main_models[idx][1])
                print(f"主模型 → {main_choice[1]}")
            elif idx < len(main_models) + len(vision_models):
                v_idx = idx - len(main_models)
                vision_choice = (vision_models[v_idx][0], vision_models[v_idx][1])
                print(f"视觉模型 → {vision_choice[1]}")
            else:
                print("无效选择。")
        except (ValueError, IndexError):
            print("无效选择。")

    return main_choice, vision_choice


def main() -> None:
    providers = load_providers()
    main_choice, vision_choice = show_menu(providers)

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
                    print("警告: 代理启动失败，视觉功能可能不可用")

    write_hermes_config(providers, main_choice, vision_choice)
    print("\n配置已写入 Hermes config.yaml")
    print("请重启 Hermes 终端使配置生效。")


if __name__ == "__main__":
    main()
