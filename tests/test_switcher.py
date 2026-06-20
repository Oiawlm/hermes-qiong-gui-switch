import unittest

from hermes_qiong_gui_switch.models import (
    BUILTIN_PROVIDERS,
    get_model_info,
    get_models_for_slot,
)
from hermes_qiong_gui_switch.switcher import build_slot_notice


class GLMVisionModelCatalogTest(unittest.TestCase):
    def test_official_glm_vision_model_is_catalogued_correctly(self):
        official_model_id = "glm-4.1v-thinking-flashx"
        old_model_id = "glm-4.1v-flashx"

        zhipu_models = BUILTIN_PROVIDERS["智谱"]["models"]
        self.assertIn(official_model_id, zhipu_models)
        self.assertNotIn(old_model_id, zhipu_models)
        self.assertEqual(
            get_model_info(official_model_id),
            {"type": "vision", "image_mode": "base64"},
        )

        main_models = [
            model_name
            for _, model_name, _ in get_models_for_slot(BUILTIN_PROVIDERS, "main")
        ]
        vision_models = [
            model_name
            for _, model_name, _ in get_models_for_slot(BUILTIN_PROVIDERS, "vision")
        ]
        self.assertNotIn(official_model_id, main_models)
        self.assertIn(official_model_id, vision_models)


class BuildSlotNoticeTest(unittest.TestCase):
    def test_vision_only_provider_is_explained_before_main_prompt(self):
        providers = {
            "火山方舟-按量": {
                "base_url": "https://example.invalid",
                "api_key": "fake",
                "models": ["deepseek-v4-pro", "doubao-seed-2.0-pro"],
            },
            "Agnes免费": {
                "base_url": "http://localhost:8899",
                "api_key": "fake",
                "models": ["agnes-2.0-flash"],
            },
        }

        notice = build_slot_notice(providers)

        self.assertIn("Agnes免费", notice)
        self.assertIn("只会在第二步出现", notice)
        self.assertIn("agnes-2.0-flash", notice)


if __name__ == "__main__":
    unittest.main()
