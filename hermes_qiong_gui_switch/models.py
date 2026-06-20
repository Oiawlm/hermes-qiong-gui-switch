"""模型能力标记 + 内置供应商配置 — 穷鬼 Switch 的知识库"""

# 内置供应商：base_url + 模型列表全部预制，用户只需填 API key
BUILTIN_PROVIDERS = {
    "火山方舟-AgentPlan": {
        "base_url": "https://ark.cn-beijing.volces.com/api/plan/v3",
        "models": ["deepseek-v4-pro", "doubao-seed-2.0-pro"],
    },
    "火山方舟-按量": {
        "base_url": "https://ark.cn-beijing.volces.com/api/plan/v3",
        "models": ["deepseek-v4-pro", "doubao-seed-2.0-pro"],
    },
    "DeepSeek官方": {
        "base_url": "https://api.deepseek.com",
        "models": ["deepseek-v4-pro"],
    },
    "智谱": {
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "models": ["glm-4.5-air", "glm-4.1v-thinking-flashx"],
    },
    "Agnes免费": {
        "base_url": "http://localhost:8899",
        "models": ["agnes-2.0-flash"],
    },
}

# 已知模型的能力标记
# type: "text"=纯文本, "vision"=纯视觉, "multimodal"=多模态
# image_mode: "base64"=原生支持, "url"=需代理转URL, None=不支持图片
KNOWN_MODELS = {
    "deepseek-v4-pro": {"type": "text", "image_mode": None},
    "deepseek-v4-flash": {"type": "text", "image_mode": None},
    "doubao-seed-2.0-pro": {"type": "multimodal", "image_mode": "base64"},
    "doubao-seed-2.0-lite": {"type": "multimodal", "image_mode": "base64"},
    "glm-4.5-air": {"type": "text", "image_mode": None},
    "glm-4.7": {"type": "text", "image_mode": None},
    "glm-4.1v-thinking-flashx": {"type": "vision", "image_mode": "base64"},
    "glm-4.6v": {"type": "vision", "image_mode": "base64"},
    "agnes-2.0-flash": {"type": "vision", "image_mode": "url"},
}


def get_model_info(model_name: str) -> dict:
    """查模型能力，未命中默认纯文本+base64"""
    return KNOWN_MODELS.get(model_name, {"type": "text", "image_mode": "base64"})


def get_models_for_slot(providers: dict, slot: str) -> list:
    """返回可用于某个槽位的模型列表。
    slot: "main"=主模型(text+multimodal), "vision"=视觉模型(vision+multimodal)
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
