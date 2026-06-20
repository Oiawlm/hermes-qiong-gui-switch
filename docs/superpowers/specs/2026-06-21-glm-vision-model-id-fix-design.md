# 智谱视觉模型代码修复设计

## 目标

修复 Hermes 穷鬼 Switch 中错误的智谱视觉模型代码，确保工具写入 Hermes 配置后能够正常调用智谱视觉 API，并通过自动测试防止同一错误再次出现。

## 已确认的根因

仓库和相关本地 Skill 使用了不存在的模型代码：

```text
glm-4.1v-flashx
```

智谱官方有效模型代码是：

```text
glm-4.1v-thinking-flashx
```

使用同一张图片、同一个智谱 API Key 和同一个 API 地址验证：

- 错误代码返回 HTTP 400，错误码 `1211`，提示模型不存在。
- 官方代码返回 HTTP 200。

Hermes 曾把错误解释成火山方舟豆包服务的 502，但实际视觉路由是智谱。该解释不作为故障依据。

## 修复范围

### 1. 仓库模型目录

修改 `hermes_qiong_gui_switch/models.py`：

- 将智谱供应商的 `glm-4.1v-flashx` 改为 `glm-4.1v-thinking-flashx`。
- 将 `KNOWN_MODELS` 中对应键同步改名。
- 保持能力标记为视觉模型、原生 base64 输入。

### 2. 自动回归测试

修改 `tests/test_switcher.py`，增加测试以确认：

- 智谱供应商包含 `glm-4.1v-thinking-flashx`。
- 仓库内置供应商不再包含 `glm-4.1v-flashx`。
- 正确模型代码被识别为 `vision` 类型。
- 正确模型代码使用 `base64` 图片模式。
- 该模型只进入视觉模型选择列表，不进入主模型选择列表。

测试只读取本地 Python 数据，不调用 API，不消耗模型额度。

### 3. 仓库文档

修改 `PLAN.md` 中出现的旧模型代码，避免设计文档继续传播错误名称。

如果 README 中没有具体模型代码，则不增加无关内容。

### 4. 本机 Hermes Skill

修正以下本地 Skill 中出现的旧代码：

- `hermes-qiong-gui-switch`
- `hermes-model-switching`
- `cc-switch-skill-management` 的相关参考资料
- `using-superpowers` 中的国产模型资料

这些文件属于本机 Hermes 的操作知识。修正它们可以避免未来代理再次根据旧资料写入错误配置。

### 5. 当前 Hermes 配置

执行前备份 `C:\Users\Lenovo\AppData\Local\hermes\config.yaml`，然后仅修改：

```yaml
auxiliary:
  vision:
    model: glm-4.1v-thinking-flashx
```

视觉模型的智谱 `base_url` 和 API Key 保持不变。主模型、其他辅助模型和其他设置不改。

## 数据流

修复后的调用路径：

```text
用户附加图片
→ Hermes vision_analyze
→ base64 图片
→ auxiliary.vision
→ glm-4.1v-thinking-flashx
→ https://open.bigmodel.cn/api/paas/v4/chat/completions
→ 返回图片描述
```

穷鬼 Switch 再次选择该视觉模型时，也会写入同一个正确代码。

## 验证方式

1. 运行完整本地测试，要求全部通过。
2. 全仓库搜索，确认旧模型代码不再出现。
3. 检查当前 Hermes 配置，确认只修改了视觉模型代码。
4. 新开 Hermes 会话，避免旧进程继续使用缓存配置。
5. 使用此前失败的同一张图片执行一次真实识图。
6. 成功标准：
   - 不再出现 HTTP 400、错误码 `1211` 或 HTML 502 页面。
   - `vision_analyze` 返回实际图片内容。

## 错误处理

- 若官方模型代码直连仍失败，保留服务端状态码和响应正文，不猜测供应商。
- 若新会话仍使用旧代码，检查是否存在未关闭的 Hermes 进程或其他配置写入来源。
- 不自动切换到 Agnes、豆包或其他视觉模型。
- 不修改 API Key，不输出 API Key。

## 非目标

- 不增加联网搜索功能。
- 不重构供应商配置格式。
- 不增加运行时在线模型目录校验。
- 不修改主模型。
- 不修改 Agnes 代理。
