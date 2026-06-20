"""Hermes 穷鬼 Switch — 主程序 CLI 菜单 + config 写入"""

import os
import sys
import yaml
from pathlib import Path

from .models import get_model_info, get_models_for_slot
from .proxy import start_proxy, is_proxy_running

HERMES_CONFIG = Path(os.environ["LOCALAPPDATA"]) / "hermes" / "config.yaml"
PROVIDERS_FILE = Path(__file__).parent.parent / "providers.yaml"


def load_providers() -> dict:
    """加载供应商配置。

    Returns:
        dict: {"provider_name": {"base_url": ..., "api_key": ..., "models": [...]}, ...}

    如果 providers.yaml 不存在，打印错误信息并退出。
    """
    if not PROVIDERS_FILE.exists():
        print(f"错误: 找不到 {PROVIDERS_FILE}")
        print("请复制 providers.yaml.example 为 providers.yaml 并填入你的 API key")
        sys.exit(1)

    with open(PROVIDERS_FILE, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    providers_list = raw.get("providers", [])

    # 支持两种格式：dict（键为供应商名）和 list（每项含 name 字段）
    if isinstance(providers_list, dict):
        return providers_list

    if isinstance(providers_list, list):
        result = {}
        for entry in providers_list:
            name = entry.pop("name", None)
            if name:
                result[name] = entry
        return result

    print("错误: providers.yaml 格式不正确，providers 应为 dict 或 list")
    sys.exit(1)


def load_current_config() -> tuple:
    """读取当前 Hermes config.yaml 中的主模型和视觉模型名称。

    Returns:
        (main_model_name, vision_model_name) 或 ("未知", "未知")
    """
    if not HERMES_CONFIG.exists():
        return "未知", "未知"

    with open(HERMES_CONFIG, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    main_model = cfg.get("model", {}).get("default", "未知")
    vision_model = cfg.get("auxiliary", {}).get("vision", {}).get("model", "未知")
    return main_model, vision_model


def write_hermes_config(providers: dict, main_choice, vision_choice) -> None:
    """将用户选择的模型写入 Hermes config.yaml。

    Args:
        providers: 供应商配置字典。
        main_choice: (provider_name, model_name) 或 None。
        vision_choice: (provider_name, model_name) 或 None。
    """
    with open(HERMES_CONFIG, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    # 主模型
    if main_choice is not None:
        pname, mname = main_choice
        pconfig = providers[pname]
        cfg["model"]["default"] = mname
        cfg["model"]["provider"] = "custom"
        cfg["model"]["base_url"] = pconfig["base_url"]
        cfg["model"]["api_key"] = pconfig["api_key"]

    # 视觉模型
    if vision_choice is not None:
        pname, mname = vision_choice
        pconfig = providers[pname]
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

    with open(HERMES_CONFIG, "w", encoding="utf-8") as f:
        yaml.dump(cfg, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


def show_menu(providers: dict) -> tuple:
    """显示 CLI 交互菜单，让用户选择主模型和视觉模型。

    Args:
        providers: 供应商配置字典。

    Returns:
        (main_choice, vision_choice)
        其中每个 choice 为 (provider_name, model_name) 或 None。
    """
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

        # 主模型列表
        print("  主模型:")
        for i, (pname, mname, _info) in enumerate(main_models, 1):
            marker = " ←" if mname == current_main else ""
            print(f"    {i}. {mname} ({pname}){marker}")

        print()
        print("  视觉模型:")
        offset = len(main_models)
        for j, (pname, mname, _info) in enumerate(vision_models, offset + 1):
            marker = " ←" if mname == current_vision else ""
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
    """主入口：加载配置 → 显示菜单 → 写入 config → 提示重启。"""
    providers = load_providers()
    main_choice, vision_choice = show_menu(providers)

    # 如果选了 Agnes 视觉模型（image_mode == "url"），确保代理在跑
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
