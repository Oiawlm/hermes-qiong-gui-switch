# Hermes 穷鬼 Switch

一键切换 Hermes Agent 的主模型和视觉模型。穷鬼专用。

## 安装

**把下面这句话发给你的 AI Agent，它会帮你搞定一切：**

> 帮我装 Hermes 穷鬼 Switch：git clone https://github.com/Oiawlm/hermes-qiong-gui-switch.git 到本地，pip install pyyaml，复制 providers.yaml.example 为 providers.yaml，然后引导我填 API key。

## 怎么用

填好 key 之后，终端里跑：

```bash
cd hermes-qiong-gui-switch
python -m hermes_qiong_gui_switch.switcher
```

输入数字选主模型和视觉模型，按 A 应用，重启 Hermes。

## 填 key

打开 `providers.yaml`，把等号右边换成你的真实 key。没有的删掉或留空。

```
火山方舟-AgentPlan=你的key
火山方舟-按量=你的key
DeepSeek官方=你的key
智谱=你的key
Agnes免费=你的key
```

## 内置供应商

base_url 和模型列表已内置，你只管填 key：

- 火山方舟 → deepseek-v4-pro + doubao-seed-2.0-pro
- DeepSeek 官方 → deepseek-v4-pro
- 智谱 → glm-4.5-air + glm-4.1v-flashx
- Agnes 免费 → agnes-2.0-flash

## 许可证

MIT
