import unittest

from hermes_qiong_gui_switch.switcher import build_slot_notice


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
