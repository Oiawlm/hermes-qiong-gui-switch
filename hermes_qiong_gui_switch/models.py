"""模型能力标记 — 穷鬼 Switch 内置的模型知识库

KNOWN_MODELS: 已知模型的精确能力标记（无自动推断，无回退猜测）
get_model_info: 查 KNOWN_MODELS，未命中返回默认值
get_models_for_slot: 从 providers 中筛选可用于指定槽位的模型
"""

# 已知模型的能力标记
# type: "text" = 纯文本, "vision" = 纯视觉, "multimodal" = 多模态（既能当主模型也能当视觉模型）
# image_mode: "base64" = 原生支持 base64, "url" = 需要代理转 URL, None = 不支持图片
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
    """获取模型能力信息。

    严格查 KNOWN_MODELS 字典。未命中时返回默认值 {"type": "text", "image_mode": "base64"}。
    不做任何自动推断，不做任何模式匹配。
    """
    if model_name in KNOWN_MODELS:
        return KNOWN_MODELS[model_name]
    return {"type": "text", "image_mode": "base64"}


def get_models_for_slot(providers: dict, slot: str) -> list:
    """返回可用于某个槽位的模型列表。

    Args:
        providers: 供应商配置字典，格式:
            {"provider_name": {"models": ["model1", "model2"], ...}, ...}
        slot: "main" = 主模型（text + multimodal）
              "vision" = 视觉模型（vision + multimodal）

    Returns:
        [(provider_name, model_name, model_info), ...]
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
