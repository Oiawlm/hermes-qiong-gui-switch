import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

from hermes_qiong_gui_switch.models import (
    BUILTIN_PROVIDERS,
    KNOWN_MODELS,
    get_model_info,
    get_models_for_slot,
)
from hermes_qiong_gui_switch.proxy import start_proxy_process
from hermes_qiong_gui_switch.switcher import (
    VISION_AUTO,
    build_slot_notice,
    config_uses_agnes_proxy,
    ensure_agnes_proxy_if_needed,
    pick_one,
    resolve_hermes_config_path,
    write_hermes_config,
)


class GLMVisionModelCatalogTest(unittest.TestCase):
    def test_official_glm_vision_model_is_catalogued_correctly(self):
        official_model_id = "glm-4.1v-thinking-flashx"
        old_model_id = "glm-4.1v-flashx"

        zhipu_models = BUILTIN_PROVIDERS["智谱"]["models"]
        self.assertIn(official_model_id, zhipu_models)
        self.assertNotIn(old_model_id, zhipu_models)
        self.assertNotIn(old_model_id, KNOWN_MODELS)
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


class AgnesModelCatalogTest(unittest.TestCase):
    def test_agnes_flash_is_available_for_main_and_vision_through_proxy(self):
        agnes_provider = BUILTIN_PROVIDERS["Agnes免费"]
        self.assertEqual(agnes_provider["base_url"], "http://localhost:8899/v1")
        self.assertIn("agnes-2.0-flash", agnes_provider["models"])
        self.assertEqual(
            get_model_info("agnes-2.0-flash"),
            {"type": "multimodal", "image_mode": "url"},
        )

        main_models = [
            model_name
            for _, model_name, _ in get_models_for_slot(BUILTIN_PROVIDERS, "main")
        ]
        vision_models = [
            model_name
            for _, model_name, _ in get_models_for_slot(BUILTIN_PROVIDERS, "vision")
        ]
        self.assertIn("agnes-2.0-flash", main_models)
        self.assertIn("agnes-2.0-flash", vision_models)


class BuildSlotNoticeTest(unittest.TestCase):
    def test_vision_only_provider_is_explained_before_main_prompt(self):
        providers = {
            "火山方舟-按量": {
                "base_url": "https://example.invalid",
                "api_key": "fake",
                "models": ["deepseek-v4-pro", "doubao-seed-2.0-pro"],
            },
            "智谱": {
                "base_url": "https://open.bigmodel.cn/api/paas/v4",
                "api_key": "fake",
                "models": ["glm-4.1v-thinking-flashx"],
            },
        }

        notice = build_slot_notice(providers)

        self.assertIn("智谱", notice)
        self.assertIn("只会在第二步出现", notice)
        self.assertIn("glm-4.1v-thinking-flashx", notice)

    def test_agnes_multimodal_provider_does_not_need_vision_only_notice(self):
        providers = {
            "Agnes免费": {
                "base_url": "http://localhost:8899/v1",
                "api_key": "fake",
                "models": ["agnes-2.0-flash"],
            },
        }

        notice = build_slot_notice(providers)

        self.assertEqual(notice, "")


class PickOneTest(unittest.TestCase):
    def test_zero_selects_vision_auto_when_enabled(self):
        with patch("builtins.input", return_value="0"):
            with patch("builtins.print"):
                choice = pick_one("vision", [], "agnes-2.0-flash", allow_auto=True)

        self.assertEqual(choice, VISION_AUTO)


class HermesConfigPathTest(unittest.TestCase):
    def test_resolves_config_path_from_hermes_config_output(self):
        completed = Mock(
            stdout=(
                "\n"
                "◆ Paths\n"
                "  Config:       D:\\HermesHome\\config.yaml\n"
                "  Secrets:      D:\\HermesHome\\.env\n"
            ),
            stderr="",
        )

        with patch("hermes_qiong_gui_switch.switcher.subprocess.run", return_value=completed):
            self.assertEqual(
                resolve_hermes_config_path(),
                Path("D:\\HermesHome\\config.yaml"),
            )

    def test_write_hermes_config_updates_explicit_config_path(self):
        with TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "actual-hermes-config.yaml"
            untouched = Path(tmpdir) / "wrong-config.yaml"
            starting_yaml = (
                "model:\n"
                "  default: deepseek-v4-pro\n"
                "  provider: custom\n"
                "  base_url: https://api.deepseek.com\n"
                "  api_key: old-main-key\n"
                "  api_mode: chat_completions\n"
                "auxiliary:\n"
                "  vision:\n"
                "    provider: main\n"
                "    model: agnes-2.0-flash\n"
                "    base_url: https://api.deepseek.com\n"
                "    api_key: old-vision-key\n"
            )
            target.write_text(starting_yaml, encoding="utf-8")
            untouched.write_text(starting_yaml, encoding="utf-8")

            providers = {
                "智谱": {
                    "base_url": "https://open.bigmodel.cn/api/paas/v4",
                    "api_key": "zhipu-key",
                    "models": ["glm-4.1v-thinking-flashx"],
                }
            }

            write_hermes_config(
                providers,
                main_choice=None,
                vision_choice=("智谱", "glm-4.1v-thinking-flashx"),
                config_path=target,
            )

            self.assertIn("glm-4.1v-thinking-flashx", target.read_text(encoding="utf-8"))
            self.assertIn("provider: custom", target.read_text(encoding="utf-8"))
            self.assertIn(
                "https://open.bigmodel.cn/api/paas/v4",
                target.read_text(encoding="utf-8"),
            )
            self.assertEqual(untouched.read_text(encoding="utf-8"), starting_yaml)

    def test_write_hermes_config_routes_agnes_main_through_proxy(self):
        with TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "config.yaml"
            target.write_text("model: {}\nauxiliary:\n  vision: {}\n", encoding="utf-8")
            providers = {
                "Agnes免费": {
                    "base_url": "http://localhost:8899/v1",
                    "api_key": "agnes-key",
                    "models": ["agnes-2.0-flash"],
                }
            }

            cfg = write_hermes_config(
                providers,
                main_choice=("Agnes免费", "agnes-2.0-flash"),
                vision_choice=None,
                config_path=target,
            )

            self.assertEqual(cfg["model"]["default"], "agnes-2.0-flash")
            self.assertEqual(cfg["model"]["base_url"], "http://localhost:8899/v1")
            self.assertEqual(cfg["model"]["api_key"], "agnes-key")
            self.assertTrue(config_uses_agnes_proxy(cfg))

    def test_write_hermes_config_syncs_custom_provider_with_main_model(self):
        with TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "config.yaml"
            target.write_text(
                "model:\n"
                "  default: old-model\n"
                "  provider: custom\n"
                "  base_url: https://old.example/v1\n"
                "  api_key: old-main-key\n"
                "  api_mode: chat_completions\n"
                "model_providers:\n"
                "  custom:\n"
                "    base_url: https://ark.cn-beijing.volces.com/api/plan/v3\n"
                "auxiliary:\n"
                "  vision: {}\n",
                encoding="utf-8",
            )
            providers = {
                "Agnes免费": {
                    "base_url": "http://localhost:8899/v1",
                    "api_key": "agnes-key",
                    "models": ["agnes-2.0-flash"],
                }
            }

            cfg = write_hermes_config(
                providers,
                main_choice=("Agnes免费", "agnes-2.0-flash"),
                vision_choice=None,
                config_path=target,
            )

            self.assertEqual(
                cfg["model_providers"]["custom"],
                {
                    "base_url": "http://localhost:8899/v1",
                    "api_key": "agnes-key",
                    "api_mode": "chat_completions",
                },
            )

    def test_write_hermes_config_resets_vision_to_auto(self):
        with TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "config.yaml"
            target.write_text(
                "model:\n"
                "  default: doubao-seed-2.0-pro\n"
                "auxiliary:\n"
                "  vision:\n"
                "    provider: custom\n"
                "    model: agnes-2.0-flash\n"
                "    base_url: http://localhost:8899/v1\n"
                "    api_key: old-key\n",
                encoding="utf-8",
            )
            providers = {}

            cfg = write_hermes_config(
                providers,
                main_choice=None,
                vision_choice=VISION_AUTO,
                config_path=target,
            )

            self.assertEqual(
                cfg["auxiliary"]["vision"],
                {"provider": "auto", "model": "", "base_url": "", "api_key": ""},
            )
            self.assertFalse(config_uses_agnes_proxy(cfg))


class AgnesProxyStartupTest(unittest.TestCase):
    def test_ensure_agnes_proxy_starts_when_final_config_references_agnes(self):
        cfg = {
            "model": {
                "default": "agnes-2.0-flash",
                "base_url": "http://localhost:8899/v1",
            }
        }
        providers = {
            "Agnes免费": {
                "api_key": "agnes-key",
                "models": ["agnes-2.0-flash"],
                "base_url": "http://localhost:8899/v1",
            }
        }

        with patch("hermes_qiong_gui_switch.switcher.is_proxy_running", side_effect=[False, True]):
            with patch("hermes_qiong_gui_switch.switcher.start_proxy_process") as start:
                with patch("hermes_qiong_gui_switch.switcher.time.sleep"):
                    with patch("builtins.print"):
                        ensure_agnes_proxy_if_needed(cfg, providers)

        start.assert_called_once_with("agnes-key")

    def test_ensure_agnes_proxy_does_not_start_without_agnes_proxy_reference(self):
        cfg = {
            "model": {
                "default": "doubao-seed-2.0-pro",
                "base_url": "https://ark.cn-beijing.volces.com/api/plan/v3",
            },
            "auxiliary": {"vision": {"provider": "auto", "model": "", "base_url": ""}},
        }
        providers = {}

        with patch("hermes_qiong_gui_switch.switcher.start_proxy_process") as start:
            ensure_agnes_proxy_if_needed(cfg, providers)

        start.assert_not_called()


class AgnesProxyProcessTest(unittest.TestCase):
    def test_start_proxy_process_launches_persistent_module_with_key_in_environment(self):
        with patch("hermes_qiong_gui_switch.proxy.subprocess.Popen") as popen:
            process = start_proxy_process("agnes-key")

        self.assertIs(process, popen.return_value)
        args = popen.call_args.args[0]
        kwargs = popen.call_args.kwargs
        self.assertEqual(args[1:4], ["-m", "hermes_qiong_gui_switch.proxy"])
        self.assertEqual(kwargs["env"]["AGNES_API_KEY"], "agnes-key")
        self.assertNotIn("agnes-key", args)


if __name__ == "__main__":
    unittest.main()
