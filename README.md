# Hermes 穷鬼 Switch

一键切换 Hermes Agent 的主模型和视觉模型。这个工具只负责把你选的模型写进 Hermes 配置里。

## 1. 事前准备：先拿 API Key

1. 这台电脑要先装好 Python。如果还没装，打开 [Python 下载页面](https://www.python.org/downloads/)，安装时勾选 `Add python.exe to PATH`。

2. 你至少准备一个供应商的 API Key。只填你有的，没用的可以留成 `你的key`。

3. 火山方舟 API Key：打开 [火山方舟控制台 API Key 页面](https://console.volcengine.com/ark/region:ark+cn-beijing/apiKey)。

4. DeepSeek API Key：打开 [DeepSeek API Keys 页面](https://platform.deepseek.com/api_keys)。

5. 智谱 API Key：打开 [智谱 API Key 页面](https://open.bigmodel.cn/usercenter/apikeys)。

6. Agnes API Key：打开 [Agnes 文档](https://agnes-ai.com/doc/quick-start)，登录后到开发者控制台创建 API Key。

7. API Key 相当于密码，不要发给别人，也不要截图发出去。

## 2. 下载这个工具

1. 打开仓库页面：[Oiawlm/hermes-qiong-gui-switch](https://github.com/Oiawlm/hermes-qiong-gui-switch)。

2. 点击绿色的 `Code` 按钮。

3. 点击 `Download ZIP`。

4. 下载完以后，把 ZIP 解压到你想放的位置，比如 `D:\app\hermes-qiong-gui-switch-main`。

5. 解压后进入这个文件夹，能看到 `providers.yaml`、`README.md` 和 `hermes_qiong_gui_switch` 文件夹就对了。

## 3. 填写 providers.yaml

1. 在解压后的文件夹里找到 `providers.yaml`。

2. 右键 `providers.yaml`，选择“用记事本打开”。如果没有这个选项，就选“打开方式”，再选“记事本”。

3. 把等号右边的 `你的key` 换成真实 API Key。等号左边不要改，等号两边不要加空格。

4. 示例：

   ```text
   火山方舟-按量=你的火山方舟key
   DeepSeek官方=你的DeepSeek key
   Agnes免费=你的Agnes key
   ```

5. 只填你有的 key。没有的那一行可以留成 `你的key`，工具会自动跳过。

6. 填完后按 `Ctrl + S` 保存，然后关闭记事本。

## 4. 在文件夹里打开命令行

1. 回到解压后的文件夹，不要进 `hermes_qiong_gui_switch` 子文件夹。

2. 在文件夹空白处按住 `Shift`，再点鼠标右键。

3. 点击“在终端中打开”或“在此处打开 PowerShell 窗口”。不同 Windows 版本名字不一样，看到哪个点哪个。

4. 如果右键菜单里没有这个选项，就点击文件夹顶部地址栏，输入 `cmd`，然后按回车。这个办法最稳。

5. 打开的窗口里，路径应该是你的工具文件夹，比如：

   ```text
   D:\app\hermes-qiong-gui-switch-main>
   ```

## 5. 安装依赖并运行

1. 先输入这行，安装依赖：

   ```powershell
   python -m pip install pyyaml
   ```

2. 再输入这行，启动切换工具：

   ```powershell
   python -m hermes_qiong_gui_switch.switcher
   ```

3. 第一步是选主模型。输入数字选模型，或者直接按回车保持不变。

4. 第二步是选视觉模型。Agnes 免费模型是视觉模型，只会在这一步出现。

5. 最后看到“确认应用？(y/n)”时，输入 `y`，然后按回车。

6. 配置写入后，重启 Hermes，让新模型生效。

## 6. 常见问题

1. 如果第一步没有 Agnes，这是正常的。Agnes 是视觉模型，不是主模型，要到第二步“视觉模型”里选。

2. 如果你填了 Agnes key，但第二步也没有 Agnes，检查 `providers.yaml` 里这一行左边是不是完全一样：

   ```text
   Agnes免费=你的key
   ```

3. 如果提示 `No module named yaml`，说明依赖没装，重新运行：

   ```powershell
   python -m pip install pyyaml
   ```

4. 如果提示 `python 不是内部或外部命令`，说明这台电脑还没装 Python，先安装 Python，再重新打开命令行窗口。

5. 如果你不知道现在在哪个文件夹，命令行里输入：

   ```powershell
   dir
   ```

   看到 `providers.yaml` 和 `hermes_qiong_gui_switch`，说明位置对。

## 7. 内置供应商

1. 火山方舟：`deepseek-v4-pro`、`doubao-seed-2.0-pro`。

2. DeepSeek 官方：`deepseek-v4-pro`。

3. 智谱：`glm-4.5-air`、`glm-4.1v-flashx`。

4. Agnes 免费：`agnes-2.0-flash`，只用于视觉模型。

## 8. 许可证

1. MIT
