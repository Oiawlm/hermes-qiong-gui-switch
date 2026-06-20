# GLM Vision Model ID Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the nonexistent `glm-4.1v-flashx` identifier with the official `glm-4.1v-thinking-flashx` identifier everywhere that can configure Hermes, protect the fix with a regression test, and verify image analysis through a fresh Hermes process.

**Architecture:** Keep the current provider catalog and switching flow unchanged. Correct the model identifier at its source in `models.py`, add a catalog-level test that exercises slot classification, synchronize repository and local Skill documentation, then update only `auxiliary.vision.model` in the live Hermes configuration after creating a backup.

**Tech Stack:** Python 3.11, `unittest`, YAML configuration, PowerShell, Hermes Agent CLI, Git

---

## File Map

- Modify `hermes_qiong_gui_switch/models.py`: authoritative built-in provider and model capability catalog.
- Modify `tests/test_switcher.py`: regression coverage for the official GLM vision identifier and slot routing.
- Modify `PLAN.md`: repository documentation that currently contains the obsolete identifier.
- Modify `C:\Users\Lenovo\.hermes\skills\hermes-qiong-gui-switch\SKILL.md`: installed project Skill catalog.
- Modify `C:\Users\Lenovo\.hermes\skills\devops\hermes-model-switching\SKILL.md`: installed Hermes switching guidance.
- Modify `C:\Users\Lenovo\.hermes\skills\devops\hermes-model-switching\references\provider-catalog.md`: installed provider reference.
- Modify `C:\Users\Lenovo\.hermes\skills\devops\cc-switch-skill-management\references\hermes-model-switching.md`: installed CC Switch reference.
- Modify `C:\Users\Lenovo\.hermes\skills\superpowers\using-superpowers\references\chinese-llm-pricing-2026.md`: installed Chinese-model reference.
- Back up and modify `C:\Users\Lenovo\AppData\Local\hermes\config.yaml`: live Hermes auxiliary vision selection.

### Task 1: Protect the Official Model Identifier with a Failing Test

**Files:**
- Modify: `tests/test_switcher.py:1-29`
- Test: `tests/test_switcher.py`

- [ ] **Step 1: Add imports for the model catalog**

Replace the import section with:

```python
import unittest

from hermes_qiong_gui_switch.models import (
    BUILTIN_PROVIDERS,
    get_model_info,
    get_models_for_slot,
)
from hermes_qiong_gui_switch.switcher import build_slot_notice
```

- [ ] **Step 2: Add the regression test**

Add this test class before `if __name__ == "__main__":`:

```python
class GLMVisionModelCatalogTest(unittest.TestCase):
    def test_official_glm_vision_model_is_catalogued_correctly(self):
        official_model = "glm-4.1v-thinking-flashx"
        obsolete_model = "glm-4.1v-flashx"
        zhipu_models = BUILTIN_PROVIDERS["智谱"]["models"]

        self.assertIn(official_model, zhipu_models)
        self.assertNotIn(obsolete_model, zhipu_models)
        self.assertEqual(
            {"type": "vision", "image_mode": "base64"},
            get_model_info(official_model),
        )

        main_pairs = {
            (provider_name, model_name)
            for provider_name, model_name, _info in get_models_for_slot(
                BUILTIN_PROVIDERS, "main"
            )
        }
        vision_pairs = {
            (provider_name, model_name)
            for provider_name, model_name, _info in get_models_for_slot(
                BUILTIN_PROVIDERS, "vision"
            )
        }

        self.assertNotIn(("智谱", official_model), main_pairs)
        self.assertIn(("智谱", official_model), vision_pairs)
```

- [ ] **Step 3: Run the new test and verify RED**

Run:

```powershell
python -m unittest tests.test_switcher.GLMVisionModelCatalogTest.test_official_glm_vision_model_is_catalogued_correctly -v
```

Expected: `FAIL` because `glm-4.1v-thinking-flashx` is not yet present in `BUILTIN_PROVIDERS["智谱"]["models"]`.

### Task 2: Correct the Repository Model Catalog

**Files:**
- Modify: `hermes_qiong_gui_switch/models.py:17-19`
- Modify: `hermes_qiong_gui_switch/models.py:30-38`
- Test: `tests/test_switcher.py`

- [ ] **Step 1: Replace the provider model identifier**

Change the 智谱 provider entry to:

```python
    "智谱": {
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "models": ["glm-4.5-air", "glm-4.1v-thinking-flashx"],
    },
```

- [ ] **Step 2: Replace the capability catalog key**

Change the corresponding `KNOWN_MODELS` entry to:

```python
    "glm-4.1v-thinking-flashx": {"type": "vision", "image_mode": "base64"},
```

- [ ] **Step 3: Run the focused test and verify GREEN**

Run:

```powershell
python -m unittest tests.test_switcher.GLMVisionModelCatalogTest.test_official_glm_vision_model_is_catalogued_correctly -v
```

Expected: `OK`.

- [ ] **Step 4: Run the complete repository test suite**

Run:

```powershell
python -m unittest discover -v
```

Expected: both the existing slot-notice test and the new GLM catalog test pass.

- [ ] **Step 5: Commit the tested code change**

Run:

```powershell
git add hermes_qiong_gui_switch/models.py tests/test_switcher.py
git commit -m "fix: correct GLM vision model id"
```

### Task 3: Synchronize Repository Documentation

**Files:**
- Modify: `PLAN.md:72`
- Modify: `PLAN.md:152`

- [ ] **Step 1: Replace both obsolete identifiers**

In `PLAN.md`, replace both occurrences of:

```text
glm-4.1v-flashx
```

with:

```text
glm-4.1v-thinking-flashx
```

- [ ] **Step 2: Verify the repository no longer contains the obsolete identifier outside historical design evidence**

Run:

```powershell
rg -n -S "glm-4\.1v-flashx" PLAN.md hermes_qiong_gui_switch README.md
```

Expected: no matches. `tests/test_switcher.py` intentionally preserves the obsolete identifier as regression evidence.

- [ ] **Step 3: Run the complete repository test suite**

Run:

```powershell
python -m unittest discover -v
```

Expected: all tests pass.

- [ ] **Step 4: Commit the repository documentation change**

Run:

```powershell
git add PLAN.md
git commit -m "docs: correct GLM vision model id"
```

### Task 4: Correct Installed Hermes Skill References

**Files:**
- Modify: `C:\Users\Lenovo\.hermes\skills\hermes-qiong-gui-switch\SKILL.md:34`
- Modify: `C:\Users\Lenovo\.hermes\skills\devops\hermes-model-switching\SKILL.md:20,27`
- Modify: `C:\Users\Lenovo\.hermes\skills\devops\hermes-model-switching\references\provider-catalog.md:30,35,56`
- Modify: `C:\Users\Lenovo\.hermes\skills\devops\cc-switch-skill-management\references\hermes-model-switching.md:35`
- Modify: `C:\Users\Lenovo\.hermes\skills\superpowers\using-superpowers\references\chinese-llm-pricing-2026.md:21,23`

- [ ] **Step 1: Create timestamped backups**

Run:

```powershell
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$backup = "C:\Users\Lenovo\.hermes\skill-backups\glm-vision-model-id-$stamp"
New-Item -ItemType Directory -Path $backup -Force | Out-Null
Copy-Item -LiteralPath 'C:\Users\Lenovo\.hermes\skills\hermes-qiong-gui-switch\SKILL.md' -Destination "$backup\hermes-qiong-gui-switch-SKILL.md"
Copy-Item -LiteralPath 'C:\Users\Lenovo\.hermes\skills\devops\hermes-model-switching\SKILL.md' -Destination "$backup\hermes-model-switching-SKILL.md"
Copy-Item -LiteralPath 'C:\Users\Lenovo\.hermes\skills\devops\hermes-model-switching\references\provider-catalog.md' -Destination "$backup\provider-catalog.md"
Copy-Item -LiteralPath 'C:\Users\Lenovo\.hermes\skills\devops\cc-switch-skill-management\references\hermes-model-switching.md' -Destination "$backup\cc-switch-hermes-model-switching.md"
Copy-Item -LiteralPath 'C:\Users\Lenovo\.hermes\skills\superpowers\using-superpowers\references\chinese-llm-pricing-2026.md' -Destination "$backup\chinese-llm-pricing-2026.md"
Write-Output "BACKUP_DIR=$backup"
```

Expected: one `BACKUP_DIR=...` line and five backup files in that directory.

- [ ] **Step 2: Replace the API identifier in all five files**

Replace every exact occurrence of:

```text
glm-4.1v-flashx
```

with:

```text
glm-4.1v-thinking-flashx
```

- [ ] **Step 3: Correct the human-readable model name**

Replace every exact occurrence of:

```text
GLM-4.1V-FlashX
```

with:

```text
GLM-4.1V-Thinking-FlashX
```

- [ ] **Step 4: Verify no installed Skill still teaches the obsolete identifier**

Run:

```powershell
rg -n -S "glm-4\.1v-flashx|GLM-4\.1V-FlashX" `
  'C:\Users\Lenovo\.hermes\skills\hermes-qiong-gui-switch' `
  'C:\Users\Lenovo\.hermes\skills\devops\hermes-model-switching' `
  'C:\Users\Lenovo\.hermes\skills\devops\cc-switch-skill-management\references\hermes-model-switching.md' `
  'C:\Users\Lenovo\.hermes\skills\superpowers\using-superpowers\references\chinese-llm-pricing-2026.md'
```

Expected: no matches.

- [ ] **Step 5: Verify the official identifier appears in every intended Skill source**

Run:

```powershell
rg -l -S "glm-4\.1v-thinking-flashx" `
  'C:\Users\Lenovo\.hermes\skills\hermes-qiong-gui-switch' `
  'C:\Users\Lenovo\.hermes\skills\devops\hermes-model-switching' `
  'C:\Users\Lenovo\.hermes\skills\devops\cc-switch-skill-management\references\hermes-model-switching.md' `
  'C:\Users\Lenovo\.hermes\skills\superpowers\using-superpowers\references\chinese-llm-pricing-2026.md'
```

Expected: the five modified files are listed.

### Task 5: Update the Live Hermes Vision Configuration Safely

**Files:**
- Back up: `C:\Users\Lenovo\AppData\Local\hermes\config.yaml`
- Modify: `C:\Users\Lenovo\AppData\Local\hermes\config.yaml:172`

- [ ] **Step 1: Create a timestamped configuration backup**

Run:

```powershell
$config = (hermes config path).Trim()
$backup = "$config.bak.glm-vision-model-id-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
Copy-Item -LiteralPath $config -Destination $backup
Write-Output "CONFIG_BACKUP=$backup"
```

Expected: one `CONFIG_BACKUP=...` line and an existing backup file.

- [ ] **Step 2: Change only the vision model identifier**

Change:

```yaml
auxiliary:
  vision:
    provider: main
    model: glm-4.1v-flashx
```

to:

```yaml
auxiliary:
  vision:
    provider: main
    model: glm-4.1v-thinking-flashx
```

Do not change `base_url`, `api_key`, timeout values, the main model, or any other setting.

- [ ] **Step 3: Prove that no other configuration value changed**

Run this read-only comparison:

```powershell
$config = (hermes config path).Trim()
$backup = Get-ChildItem -LiteralPath (Split-Path $config) -Filter 'config.yaml.bak.glm-vision-model-id-*' |
  Sort-Object LastWriteTime -Descending |
  Select-Object -First 1
& 'C:\Users\Lenovo\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe' -c "import sys,yaml; old=yaml.safe_load(open(sys.argv[1],encoding='utf-8')); new=yaml.safe_load(open(sys.argv[2],encoding='utf-8')); old_model=old['auxiliary']['vision'].pop('model'); new_model=new['auxiliary']['vision'].pop('model'); assert old_model=='glm-4.1v-flashx', old_model; assert new_model=='glm-4.1v-thinking-flashx', new_model; assert old==new, 'Configuration changed outside auxiliary.vision.model'; print('ONLY_VISION_MODEL_CHANGED')" $backup.FullName $config
```

Expected:

```text
ONLY_VISION_MODEL_CHANGED
```

- [ ] **Step 4: Confirm the effective auxiliary route without exposing credentials**

Run:

```powershell
& 'C:\Users\Lenovo\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe' -c "from agent.auxiliary_client import _resolve_task_provider_model; p,m,b,k,a=_resolve_task_provider_model('vision'); print('provider='+str(p)); print('model='+str(m)); print('base_url='+str(b)); print('key_set='+str(bool(k)))"
```

Working directory:

```text
C:\Users\Lenovo\AppData\Local\hermes\hermes-agent
```

Expected:

```text
provider=custom
model=glm-4.1v-thinking-flashx
base_url=https://open.bigmodel.cn/api/paas/v4
key_set=True
```

### Task 6: Verify Real Image Analysis Through a Fresh Hermes Process

**Files:**
- Read: `C:\Users\Lenovo\AppData\Local\hermes\images\clip_20260620_235503_1.png`
- Read: `C:\Users\Lenovo\AppData\Local\hermes\logs\agent.log`

- [ ] **Step 1: Confirm the original image still exists**

Run:

```powershell
Get-Item -LiteralPath 'C:\Users\Lenovo\AppData\Local\hermes\images\clip_20260620_235503_1.png' | Select-Object FullName,Length,LastWriteTime
```

Expected: the PNG exists and has nonzero length.

- [ ] **Step 2: Start a fresh one-shot Hermes process and require the vision tool**

Run:

```powershell
hermes --ignore-rules -t vision -z "Use vision_analyze on C:\Users\Lenovo\AppData\Local\hermes\images\clip_20260620_235503_1.png. Return one concise Chinese sentence describing what is visible in the image."
```

Expected: a Chinese description of the image, not `1211`, `502 Bad Gateway`, `模型不存在`, or `vision analysis failed`.

- [ ] **Step 3: Verify the fresh log contains the corrected route and no original symptom**

Run:

```powershell
hermes logs --since 5m | Select-String -Pattern 'glm-4.1v-thinking-flashx|vision_analyze|1211|502 Bad Gateway|模型不存在' -Context 1,2
```

Expected: evidence of successful vision analysis using the corrected identifier, with no new `1211` or HTML 502 failure for the fresh session.

### Task 7: Final Verification and Repository Status

**Files:**
- Verify: repository and installed Skill files listed above

- [ ] **Step 1: Run all repository tests again**

Run:

```powershell
python -m unittest discover -v
```

Expected: all tests pass with zero failures and zero errors.

- [ ] **Step 2: Verify the obsolete identifier is absent from active code and operational guidance**

Run:

```powershell
rg -n -S "glm-4\.1v-flashx" `
  PLAN.md `
  hermes_qiong_gui_switch `
  'C:\Users\Lenovo\.hermes\skills\hermes-qiong-gui-switch' `
  'C:\Users\Lenovo\.hermes\skills\devops\hermes-model-switching' `
  'C:\Users\Lenovo\.hermes\skills\devops\cc-switch-skill-management\references\hermes-model-switching.md' `
  'C:\Users\Lenovo\.hermes\skills\superpowers\using-superpowers\references\chinese-llm-pricing-2026.md'
```

Expected: no matches. The approved design and implementation plan are excluded because they intentionally preserve the obsolete identifier as historical failure evidence. `tests/test_switcher.py` also intentionally preserves the obsolete identifier as `assertNotIn` regression evidence.

- [ ] **Step 3: Inspect repository history and working tree**

Run:

```powershell
git log -5 --oneline --decorate
git status --short
```

Expected: commits for the implementation plan, tested code fix, and documentation correction are present; the repository working tree is clean.

- [ ] **Step 4: Report the verified outcome**

Report separately:

- Current status: whether the same image now analyzes successfully.
- Root cause: nonexistent `glm-4.1v-flashx` identifier propagated by the repository and local Skills.
- Repair: official identifier, regression test, synchronized Skills, backed-up live configuration.
- Evidence: test count, real Hermes output, backup paths, and commit hashes.
