# Hermes 穷鬼 Switch

一键切换 Hermes 模型供应商。

## 安装

```bash
git clone <repo-url>
cd hermes-qiong-gui-switch
cp providers.yaml.example providers.yaml
# 编辑 providers.yaml，填入你的 API key
```

## 使用

```bash
python -m hermes_qiong_gui_switch.switcher
```

> **注意：** 切换完成后需要重启 Hermes 才能生效。
