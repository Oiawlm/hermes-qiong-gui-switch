# Hermes 穷鬼 Switch

一键切换 Hermes Agent 的主模型和视觉模型供应商。穷鬼专用。

## 功能

- 独立选择主模型和视觉模型，跨供应商混搭
- 自动处理 base64/URL 图片模式差异
- 选 Agnes 免费模型时自动启动本地代理
- 一键写入 Hermes config.yaml

## 安装

```bash
git clone https://github.com/Oiawlm/hermes-qiong-gui-switch.git
cd hermes-qiong-gui-switch
pip install pyyaml
cp providers.yaml.example providers.yaml
```

编辑 `providers.yaml`，填入你的 API key。

## 使用

```bash
python -m hermes_qiong_gui_switch.switcher
```

1. 输入数字选择主模型
2. 输入数字选择视觉模型（可选）
3. 按 A 应用配置
4. 重启 Hermes 终端

## 供应商配置

在 `providers.yaml` 中添加你的供应商：

```yaml
providers:
  我的供应商:
    base_url: https://api.example.com/v1
    api_key: sk-xxx
    models:
      - model-name-1
      - model-name-2
```

工具内置了常见模型的能力标记（纯文本/多模态/视觉），未知模型默认为纯文本。

## 注意事项

- `providers.yaml` 包含 API key，已在 .gitignore 中，不会被提交
- 切换后需重启 Hermes 终端
- Agnes 模型需要本地代理（工具自动启动）

## 许可证

MIT
