# GIF → MP4

一个轻量的本地 GIF 转 MP4 小工具。HTML 拖拽入口，转换后自动保存到系统下载目录。

**原生 HTML / CSS / JavaScript + Python 标准库 + 已安装的 FFmpeg。** 无前端框架，无 pip / npm 依赖，无 CDN，无在线上传，不捆绑运行时或 FFmpeg。

## 使用

1. 安装或复用已有的 Python 和 FFmpeg（配置见下文）。
2. 下载本仓库并解压，运行对应系统的启动脚本。
3. 浏览器自动打开 `http://127.0.0.1:18746`。
4. 拖入 GIF，或点击选择文件。转换完成后，页面会显示实际保存路径。

可一次选择多个 GIF，按顺序处理。同名自动加 `(1)`、`(2)`，不覆盖现有文件。

服务启动后也可以双击 `index.html`，它会跳转到本地页面。**HTML 本身不能启动 Python，也不能绕过浏览器限制直接写下载目录**，因此首次使用或关闭服务后，需要先运行启动脚本。使用期间保持终端窗口开启，关闭窗口或按 `Ctrl+C` 停止服务。

## 环境要求

- Python **3.9+**。
- FFmpeg **5+**，构建中须包含 `libx264` 编码器。
- 现代桌面浏览器。
- 无需虚拟环境，无需运行 `pip install` 或 `npm install`。

先检查已有环境，不需要重复安装：

```sh
python3 --version
ffmpeg -version
ffmpeg -hide_banner -encoders
```

Windows 的 Python 检查可使用 `py -3 --version`。编码器列表中应包含 `libx264`。

## 各系统配置

| 系统 | 启动入口 | 默认输出位置 | 验证状态 |
| --- | --- | --- | --- |
| macOS（Apple Silicon / Intel） | 双击 `启动.command` | `~/Downloads` | Apple Silicon 实机验证；Intel 未实机验证 |
| Windows | 双击 `start.bat` | Windows 注册表记录的 Downloads 目录，支持重定向目录 | 已适配，未实机验证 |
| Linux 桌面 | `sh start.sh` | `xdg-user-dir DOWNLOAD`，无该命令时使用 `~/Downloads` | 已适配，未实机验证 |

### macOS

如果已经安装 Homebrew，可安装缺失组件：

```sh
brew install python ffmpeg
```

双击 `启动.command`。启动脚本同时查找 Apple Silicon 的 `/opt/homebrew/bin` 和 Intel 的 `/usr/local/bin`，也会保留现有 PATH。

如果下载 ZIP 后执行权限丢失，可在项目文件夹中运行：

```sh
sh 启动.command
```

也可以直接运行 `python3 server.py`。如果系统阻止打开下载的脚本，可先检查源码，再从终端运行；无需关闭系统安全机制。

### Windows

1. 从 [Python 官方网站](https://www.python.org/downloads/windows/) 安装 Python，确保 `py -3` 或 `python` 可用。
2. 从 [FFmpeg 官方下载页](https://ffmpeg.org/download.html) 选择 Windows 构建，解压后将含 `ffmpeg.exe` 的 `bin` 文件夹加入用户 PATH。
3. 重新打开终端，确认 `ffmpeg -version` 成功。
4. 双击 `start.bat`，或在项目目录运行 `py -3 server.py`。

启动脚本优先使用 `py -3`，没有 Python Launcher 时使用 `python`。若 `python` 打开 Microsoft Store，说明可执行文件尚未正确配置，请完成 Python 安装或使用 `py -3`。

### Linux

Debian / Ubuntu 示例：

```sh
sudo apt update
sudo apt install python3 ffmpeg xdg-user-dirs xdg-utils
sh start.sh
```

其他发行版通过自己的包管理器安装对应软件，并确认 FFmpeg 含 `libx264`。`xdg-user-dirs` 用于识别本地化的下载目录，`xdg-utils` 提供“打开 Downloads”所用的 `xdg-open`。

本工具面向本机桌面环境。无桌面环境时可以手动访问打印出的本地地址，但“打开 Downloads”需要桌面文件管理器。

## 可选配置

默认从 PATH 查找 FFmpeg。如果使用便携版或自定义输出目录，可以设置环境变量，不必修改源码。

| 环境变量 | 用途 |
| --- | --- |
| `FFMPEG_BINARY` | FFmpeg 可执行文件的完整路径 |
| `GIF_MP4_DOWNLOADS` | 自定义输出文件夹；不存在时自动创建 |

macOS / Linux：

```sh
FFMPEG_BINARY="/path/to/ffmpeg" GIF_MP4_DOWNLOADS="$HOME/Downloads" python3 server.py
```

Windows PowerShell：

```powershell
$env:FFMPEG_BINARY = 'C:\tools\ffmpeg\bin\ffmpeg.exe'
$env:GIF_MP4_DOWNLOADS = 'D:\Videos'
py -3 server.py
```

## 转换行为

- H.264 / `yuv420p` MP4，`CRF 18`，`fast` 预设，启用 faststart。
- 读取 GIF 一轮动画，不重复展开 GIF 的无限循环。
- 使用可变帧率保留 GIF 时间信息；容器时间基可能产生舍入。
- 不缩放画面。奇数宽高在右侧或底部最多补 1 像素，使 H.264 输出尺寸为偶数。
- 不生成音轨。MP4 不支持 GIF 的透明通道，透明效果不会保留。
- GIF 临时文件在转换结束后清除；失败时移除本次未完成的 MP4。
- 上传流写入临时文件，前端按顺序转换，避免同时启动多个编码任务。

## 本地与隐私

服务仅监听 `127.0.0.1`，文件从浏览器传给本机 Python，再由本机 FFmpeg 处理。页面不引用远程资源，也不收集数据。写入请求使用每次启动生成的随机令牌。

这是个人桌面工具，不是面向公网的上传服务。请保持默认的本机监听地址，不要通过端口转发对外开放。不支持 GitHub Pages 单独运行：自动写入下载目录依赖本地服务。

## 常见问题

- **找不到 FFmpeg**：确认 `ffmpeg -version` 可运行，或设置 `FFMPEG_BINARY`；安装后重新启动终端。
- **Unknown encoder 'libx264'**：换用包含 libx264 的 FFmpeg 构建。
- **页面连接失败**：先运行启动脚本，保持终端窗口开启，然后刷新页面。
- **端口 18746 已占用**：已有本工具运行时会打开原页面；若被其他程序占用，先停止该程序再启动。
- **重复启动后没有加载新代码**：先停止原服务再启动。页面刷新只更新 HTML，不会重载 Python 进程。
- **无法打开下载文件夹**：文件可能已经转换成功，可按页面显示的路径手动打开；Linux 还需安装 `xdg-utils` 并处于桌面会话中。
- **下载目录无写入权限**：调整目录权限或通过 `GIF_MP4_DOWNLOADS` 指定可写文件夹。
- **文件较大、转换时间长**：速度取决于分辨率、时长和本机 CPU；当前没有百分比进度条或取消按钮。

## 项目结构

```text
index.html      拖拽页面、文件选择与转换队列
server.py       本地 HTTP 服务与 FFmpeg 调用
启动.command    macOS 启动脚本
start.bat       Windows 启动脚本
start.sh        Linux 启动脚本
```

源码保持小而直接，未捆绑二进制文件。当前在 macOS 上验证过实际转换、奇数尺寸补齐、单轮时长、同名文件保护和错误输入处理。Windows / Linux 分支尚未进行实机验证，欢迎带系统版本和错误日志提交 Issue；请勿附带隐私文件。
