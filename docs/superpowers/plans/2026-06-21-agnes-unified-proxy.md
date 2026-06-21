# Agnes Unified Proxy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `agnes-2.0-flash` selectable as both a Hermes main model and vision auxiliary model, with every Agnes slot routed through the local base64-to-URL proxy.

**Architecture:** Treat Agnes as a multimodal URL-image model in the catalog and expose `http://localhost:8899/v1` as its configured Hermes endpoint. Refactor config writing into read/build/save helpers so the CLI can compute the final config, start the Agnes proxy when that final config references it, then write the config. Add an explicit vision auto option that resets stale explicit vision configuration.

**Tech Stack:** Python 3, `unittest`, YAML config via `pyyaml`, PowerShell, Hermes CLI config files

---

## File Map

- Modify `hermes_qiong_gui_switch/models.py`: Agnes provider endpoint and capability metadata.
- Modify `hermes_qiong_gui_switch/switcher.py`: vision auto sentinel, config build helpers, final-config proxy-start decision, CLI prompt behavior.
- Modify `tests/test_switcher.py`: catalog, config, vision auto, and proxy-start regression tests.
- Modify `README.md`: user-facing explanation that Agnes appears in both slots and that Agnes uses the local proxy for compatibility.

### Task 1: Add Agnes Catalog Regression Coverage

**Files:**
- Modify: `tests/test_switcher.py`
- Test: `tests/test_switcher.py`

- [ ] **Step 1: Add a failing catalog test**

Add this test class after `GLMVisionModelCatalogTest`:

```python
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
```

- [ ] **Step 2: Run the focused test and verify RED**

Run:

```powershell
python -m unittest tests.test_switcher.AgnesModelCatalogTest.test_agnes_flash_is_available_for_main_and_vision_through_proxy -v
```

Expected: FAIL because the existing catalog uses `http://localhost:8899` and marks Agnes as `vision`.

### Task 2: Implement Agnes Catalog Change

**Files:**
- Modify: `hermes_qiong_gui_switch/models.py`
- Test: `tests/test_switcher.py`

- [ ] **Step 1: Update the Agnes provider endpoint and capability**

Change the Agnes provider and known model entry to:

```python
    "Agnes免费": {
        "base_url": "http://localhost:8899/v1",
        "models": ["agnes-2.0-flash"],
    },
```

```python
    "agnes-2.0-flash": {"type": "multimodal", "image_mode": "url"},
```

- [ ] **Step 2: Run the focused test and verify GREEN**

Run:

```powershell
python -m unittest tests.test_switcher.AgnesModelCatalogTest.test_agnes_flash_is_available_for_main_and_vision_through_proxy -v
```

Expected: OK.

### Task 3: Add Config and Proxy Behavior Tests

**Files:**
- Modify: `tests/test_switcher.py`
- Test: `tests/test_switcher.py`

- [ ] **Step 1: Import new switcher helpers**

Extend the switcher import block to include:

```python
    VISION_AUTO,
    config_uses_agnes_proxy,
    ensure_agnes_proxy_if_needed,
```

- [ ] **Step 2: Add config tests**

Add these tests to `HermesConfigPathTest`:

```python
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
```

- [ ] **Step 3: Add proxy-start tests**

Add this test class before `AgnesProxyProcessTest`:

```python
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
```

- [ ] **Step 4: Run new tests and verify RED**

Run:

```powershell
python -m unittest tests.test_switcher.HermesConfigPathTest.test_write_hermes_config_routes_agnes_main_through_proxy tests.test_switcher.HermesConfigPathTest.test_write_hermes_config_resets_vision_to_auto tests.test_switcher.AgnesProxyStartupTest -v
```

Expected: errors or failures because the helper constants/functions do not exist and `write_hermes_config` does not return the config.

### Task 4: Implement Config Helpers, Vision Auto, and Proxy Startup

**Files:**
- Modify: `hermes_qiong_gui_switch/switcher.py`
- Test: `tests/test_switcher.py`

- [ ] **Step 1: Add constants and helper functions**

Add near the top of `switcher.py`:

```python
import time
```

Add after file constants:

```python
VISION_AUTO = "__vision_auto__"
AGNES_MODEL = "agnes-2.0-flash"
AGNES_PROXY_BASE_URL = "http://localhost:8899/v1"
```

Add config helpers:

```python
def load_config_dict(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def apply_model_choices(cfg: dict, providers: dict, main_choice, vision_choice) -> dict:
    cfg.setdefault("model", {})
    cfg.setdefault("auxiliary", {}).setdefault("vision", {})

    if main_choice is not None:
        pname, mname = main_choice
        pconfig = providers[pname]
        cfg["model"]["default"] = mname
        cfg["model"]["provider"] = "custom"
        cfg["model"]["base_url"] = pconfig["base_url"]
        cfg["model"]["api_key"] = pconfig["api_key"]

    if vision_choice == VISION_AUTO:
        cfg["auxiliary"]["vision"] = {
            "provider": "auto",
            "model": "",
            "base_url": "",
            "api_key": "",
        }
    elif vision_choice is not None:
        pname, mname = vision_choice
        pconfig = providers[pname]
        cfg["auxiliary"]["vision"]["model"] = mname
        cfg["auxiliary"]["vision"]["provider"] = "custom"
        cfg["auxiliary"]["vision"]["api_key"] = pconfig["api_key"]
        cfg["auxiliary"]["vision"]["base_url"] = pconfig["base_url"]

    return cfg
```

Add proxy helpers:

```python
def config_uses_agnes_proxy(cfg: dict) -> bool:
    sections = [cfg.get("model", {}), cfg.get("auxiliary", {}).get("vision", {})]
    for section in sections:
        base_url = str(section.get("base_url", "")).rstrip("/")
        if section.get("model") == AGNES_MODEL or section.get("default") == AGNES_MODEL:
            if base_url == AGNES_PROXY_BASE_URL.rstrip("/"):
                return True
    return False


def get_agnes_api_key(providers: dict) -> str:
    for pconfig in providers.values():
        if AGNES_MODEL in pconfig.get("models", []):
            return pconfig.get("api_key", "")
    return ""


def ensure_agnes_proxy_if_needed(cfg: dict, providers: dict) -> None:
    if not config_uses_agnes_proxy(cfg):
        return
    if is_proxy_running():
        return
    agnes_key = get_agnes_api_key(providers)
    if not agnes_key:
        print("警告: Agnes 代理需要 API key，但 providers.yaml 中没有可用的 Agnes key")
        return
    print("启动 Agnes 代理...")
    start_proxy_process(agnes_key)
    time.sleep(1)
    if is_proxy_running():
        print("代理已启动 (localhost:8899)")
    else:
        print("警告: 代理启动失败")
```

- [ ] **Step 2: Refactor `write_hermes_config` to return the written config**

Replace its config-load and slot-write body with:

```python
    path = Path(config_path) if config_path is not None else resolve_hermes_config_path()
    cfg = load_config_dict(path)
    cfg = apply_model_choices(cfg, providers, main_choice, vision_choice)

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(cfg, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    return cfg
```

- [ ] **Step 3: Add vision auto to `pick_one`**

Change `pick_one` to accept `allow_auto=False`. When `allow_auto` is true, print `0. 跟随主模型 / 自动`; when the user enters `0`, return `VISION_AUTO`.

- [ ] **Step 4: Use final config in `main` before writing**

Replace the manual proxy startup block with:

```python
    planned_cfg = apply_model_choices(
        load_config_dict(config_path),
        providers,
        main_choice,
        vision_choice,
    )
    ensure_agnes_proxy_if_needed(planned_cfg, providers)
    write_hermes_config(providers, main_choice, vision_choice, config_path=config_path)
```

- [ ] **Step 5: Run focused tests and verify GREEN**

Run:

```powershell
python -m unittest tests.test_switcher.HermesConfigPathTest.test_write_hermes_config_routes_agnes_main_through_proxy tests.test_switcher.HermesConfigPathTest.test_write_hermes_config_resets_vision_to_auto tests.test_switcher.AgnesProxyStartupTest -v
```

Expected: OK.

### Task 5: Update Existing Slot Notice Test and README

**Files:**
- Modify: `tests/test_switcher.py`
- Modify: `README.md`

- [ ] **Step 1: Update the old Agnes vision-only notice test**

Change the test to use `glm-4.1v-thinking-flashx` as the vision-only model and expect `Agnes` not to appear in the notice when it is multimodal.

- [ ] **Step 2: Update README wording**

Replace the user-facing statements that Agnes only appears in the second step. State that Agnes appears in both main and vision choices, and that the tool uses the local proxy automatically for Agnes compatibility.

- [ ] **Step 3: Search for stale wording**

Run:

```powershell
rg -n "Agnes.*只|只.*Agnes|不是主模型|只会.*第二步|视觉模型 \\|" README.md hermes_qiong_gui_switch tests docs
```

Expected: no active user-facing docs claim Agnes is vision-only. Historical design docs may mention the old state as context.

### Task 6: Final Verification

**Files:**
- Verify all modified files.

- [ ] **Step 1: Run the full unit test suite**

Run:

```powershell
python -m unittest discover -v
```

Expected: all tests pass.

- [ ] **Step 2: Inspect diff and status**

Run:

```powershell
git diff --stat
git status --short
```

Expected: only planned files are modified.

- [ ] **Step 3: Commit implementation**

Run:

```powershell
git add hermes_qiong_gui_switch/models.py hermes_qiong_gui_switch/switcher.py tests/test_switcher.py README.md docs/superpowers/plans/2026-06-21-agnes-unified-proxy.md
git commit -m "feat: route Agnes model slots through proxy"
```
