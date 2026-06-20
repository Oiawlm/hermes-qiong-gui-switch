# Hermes 穷鬼 Switch

一键切换 Hermes Agent 的主模型和视觉模型。穷鬼专用。

## 怎么用

**第一步：填 key**

复制 `providers.yaml.example` 为 `providers.yaml`，把等号右边换成你的真实 API key。没有的删掉或留空。

```
火山方舟-AgentPlan=ark-7e5d...
DeepSeek官方=sk-xxx
智谱=你的key
Agnes免费=sk-P7j...
```

**第二步：运行**

```bash
pip install pyyaml
python -m hermes_qiong_gui_switch.switcher
```

**第三步：选模型**

输入数字选主模型和视觉模型，按 A 应用，重启 Hermes。

## 内置供应商

base_url 和模型列表已内置，你只管填 key：

- 火山方舟 Agent Plan / 按量 → deepseek-v4-pro + doubao-seed-2.0-pro
- DeepSeek 官方 → deepseek-v4-pro
- 智谱 → glm-4.5-air + glm-4.1v-flashx
- Agnes 免费 → agnes-2.0-flash（自动启动代理）

## 许可证

MIT
