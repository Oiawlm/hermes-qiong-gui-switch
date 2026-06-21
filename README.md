# Hermes 穷鬼 Switch

一键切换 Hermes Agent 的主模型和视觉模型。这个工具只负责把你选的模型写进 Hermes 配置里。

如果你已经装过旧版，想更新到最新版本，先看下面的“四、如何更新到最新版”。

## 一、快速开始

### 1. 下载 ZIP

打开这个仓库页面：[Oiawlm/hermes-qiong-gui-switch](https://github.com/Oiawlm/hermes-qiong-gui-switch)。

点击绿色的 `Code` 按钮，再点击 `Download ZIP`。

### 2. 解压文件夹

把下载好的 ZIP 解压到你想放的位置，比如：

```text
D:\app\hermes-qiong-gui-switch-main
```

解压后进入这个文件夹，能看到下面这些东西就对了：

```text
providers.yaml
README.md
hermes_qiong_gui_switch
```

### 3. 填写 providers.local.yaml

`providers.yaml` 是公开模板，更新工具时可能会跟着仓库一起变化。建议先复制一份本地配置：

右键 `providers.yaml`，选择“复制”，再在同一个文件夹空白处右键“粘贴”，把新文件重命名为：

```text
providers.local.yaml
```

如果这个文件已经存在，就直接用它，不用重新复制。

右键 `providers.local.yaml`，选择“用记事本打开”。如果没有这个选项，就选“打开方式”，再选“记事本”。

把等号右边的 `你的key` 换成真实 API Key。等号左边不要改，等号两边不要加空格。

示例：

```text
火山方舟-按量=你的火山方舟key
DeepSeek官方=你的DeepSeek key
Agnes免费=你的Agnes key
```

只填你有的 key。没有的那一行可以留成 `你的key`，工具会自动跳过。

填完后按 `Ctrl + S` 保存，然后关闭记事本。

`providers.local.yaml` 只放在你自己的电脑里，里面可能有真实 API Key，不要发给别人，也不要上传到自己的 GitHub 仓库。

### 4. 打开命令行

回到解压后的文件夹，不要进 `hermes_qiong_gui_switch` 子文件夹。

在文件夹空白处按住 `Shift`，再点鼠标右键。

点击“在终端中打开”或“在此处打开 PowerShell 窗口”。不同 Windows 版本名字不一样，看到哪个点哪个。

如果右键菜单里没有这个选项，就点击文件夹顶部地址栏，输入 `cmd`，然后按回车。这个办法最稳。

打开的窗口里，路径应该是你的工具文件夹，比如：

```text
D:\app\hermes-qiong-gui-switch-main>
```

### 5. 运行切换工具

输入：

```powershell
python -m hermes_qiong_gui_switch.switcher
```

第一步是选主模型。输入数字选模型，或者直接按回车保持不变。

第二步是选视觉模型。Agnes 免费模型也会出现在这里；如果想让 Hermes 自动跟随主模型处理图片，可以输入 `0`。

最后看到“确认应用？(y/n)”时，输入 `y`，然后按回车。

配置写入后，重启 Hermes，让新模型生效。

## 二、选择模型怎么看

### 1. 主模型是什么

主模型就是 Hermes 平时聊天、写代码、处理大多数任务时用的模型。

你会在第一步看到主模型列表，比如 `deepseek-v4-pro`、`doubao-seed-2.0-pro`。

### 2. 视觉模型是什么

视觉模型是 Hermes 看图片时用的模型。

如果你不处理图片，可以直接按回车跳过视觉模型，不影响主模型切换。

### 3. Agnes 为什么主模型和视觉模型里都有

Agnes 免费模型既可以作为主模型使用，也可以作为视觉模型使用。

为了兼容 Hermes 发送的 base64 图片，工具会让 Agnes 统一走本地代理 `localhost:8899`。普通文本会直接转发给 Agnes；遇到图片时，代理会先把图片转成 Agnes 支持的公开 URL。

## 三、供应商和 API Key

| 供应商 | providers.yaml 里的名字 | 用途 | API Key 链接 |
| --- | --- | --- | --- |
| 火山方舟 AgentPlan | `火山方舟-AgentPlan` | 主模型 / 视觉模型 | [火山方舟 API Key](https://console.volcengine.com/ark/region:ark+cn-beijing/apiKey) |
| 火山方舟按量 | `火山方舟-按量` | 主模型 / 视觉模型 | [火山方舟 API Key](https://console.volcengine.com/ark/region:ark+cn-beijing/apiKey) |
| DeepSeek 官方 | `DeepSeek官方` | 主模型 | [DeepSeek API Keys](https://platform.deepseek.com/api_keys) |
| 智谱 | `智谱` | 主模型 / 视觉模型 | [智谱 API Key](https://open.bigmodel.cn/usercenter/apikeys) |
| Agnes 免费 | `Agnes免费` | 主模型 / 视觉模型 | [Agnes 文档](https://agnes-ai.com/doc/quick-start) |

API Key 相当于密码，不要发给别人，也不要截图发出去。

## 四、如何更新到最新版

先看你当初是怎么安装的：

- 如果你是点 GitHub 的 `Download ZIP` 下载的，按“ZIP 方式更新”。
- 如果你是用 `git clone` 下载的，按“Git 方式更新”。

### 1. ZIP 方式更新

不要把新 ZIP 直接解压覆盖旧文件夹。这样容易把自己填过的配置搞乱。

推荐做法：

1. 打开仓库页面：[Oiawlm/hermes-qiong-gui-switch](https://github.com/Oiawlm/hermes-qiong-gui-switch)。
2. 点击绿色的 `Code` 按钮，再点击 `Download ZIP`。
3. 把新 ZIP 解压成一个新的文件夹。
4. 从旧文件夹复制 `providers.local.yaml` 到新文件夹。
5. 如果旧文件夹没有 `providers.local.yaml`，就打开旧的 `providers.yaml`，把你填过的 API Key 复制到新文件夹的 `providers.local.yaml`。
6. 在新文件夹里重新运行：

```powershell
python -m hermes_qiong_gui_switch.switcher
```

确认新版本能正常使用后，再删除旧文件夹。

### 2. Git 方式更新

如果你之后想更新得更省事，可以第一次就用 Git 下载：

```powershell
git clone https://github.com/Oiawlm/hermes-qiong-gui-switch.git
```

进入下载好的文件夹后，先复制一份本地配置：

```powershell
Copy-Item providers.yaml providers.local.yaml
notepad providers.local.yaml
```

把 `providers.local.yaml` 里的 `你的key` 换成自己的真实 API Key。

以后更新时，只需要在工具文件夹里运行：

```powershell
git pull --ff-only
```

如果你以前按旧说明直接把 key 填在 `providers.yaml` 里，先把它复制成 `providers.local.yaml`，确认 key 已经在 `providers.local.yaml` 里，再让 `providers.yaml` 回到仓库模板：

```powershell
Copy-Item providers.yaml providers.local.yaml
git restore providers.yaml
git pull --ff-only
```

然后照常运行：

```powershell
python -m hermes_qiong_gui_switch.switcher
```

`providers.local.yaml` 已经在这个仓库的 `.gitignore` 里，不会被正常的 Git 提交带上。这里提醒“不要上传”，是给 fork 仓库或自己改代码的用户看的：不要手动把带真实 API Key 的文件上传到自己的 GitHub，也不要把这个文件发给别人。

## 五、常见问题

### 1. 提示 python 不是内部或外部命令

这说明这台电脑还没装 Python，或者安装时没有加入 PATH。

打开 [Python 下载页面](https://www.python.org/downloads/) 安装 Python。安装时勾选 `Add python.exe to PATH`。

安装完以后，关掉命令行窗口，重新在工具文件夹里打开命令行。

### 2. 提示 No module named yaml

这说明缺少 `pyyaml`。

输入：

```powershell
python -m pip install pyyaml
```

安装完以后，重新运行：

```powershell
python -m hermes_qiong_gui_switch.switcher
```

### 3. Agnes 没出现

如果第一步和第二步都没有 Agnes，检查 `providers.yaml` 里这一行左边是不是完全一样：

如果只是不想继续显式使用 Agnes 视觉模型，第二步输入 `0` 可以恢复为“跟随主模型 / 自动”。

```text
Agnes免费=你的key
```

不要写成“安卓斯”“安格鲁斯”，也不要在等号两边加空格。

### 4. 不知道当前文件夹对不对

命令行里输入：

```powershell
dir
```

看到 `providers.yaml` 和 `hermes_qiong_gui_switch`，说明位置对。

## 六、许可证

MIT
