> readme目前是ai写的( 如果有问题的话 记得联系我改(

# 祈福签 API - Python 版本

基于 FastAPI + Pillow 实现的sky祈福签图片生成 API

## 技术栈

- **Python**: 3.12+
- **FastAPI**: Web 框架
- **Pillow**: 图像处理
- **Uvicorn**: ASGI 服务器
- **TOML**: 配置文件解析

## 快速开始

### 1. 安装依赖

```powershell
# 创建虚拟环境
python -m venv venv  # Windows
python3 -m venv venv  # Linux/macOS

# 激活虚拟环境 并打印一下解释器路径 确保虚拟环境激活
.\venv\Scripts\activate  # Windows
Get-Command python # Windows PowerShell
source venv/bin/activate  # Linux/macOS
which python # Linux bash

# 安装依赖
# pip install fastapi uvicorn pillow python-multipart toml
pip install -r ./requirements.txt
```

### 2. 配置文件

编辑 `config.toml`:

```toml
[server]
host = "0.0.0.0"
port = 51205
log_level = "debug"  # "info" 或 "debug"

[image]
width = 1240
height = 620
font_size = 40
assets_dir = "../assets"
```

### 3. 运行服务

```powershell
cd src
python main.py
```

或使用 uvicorn 直接运行：

```powershell
cd src
uvicorn main:app --host 0.0.0.0 --port 51205
# --reload可选
uvicorn main:app --host 0.0.0.0 --port 51205 --reload
```

### 4. 访问 API

- **主页**: http://localhost:51205/
- **获取祈福签**: http://localhost:51205/blessing
- **API 文档**: http://localhost:51205/docs

## 项目结构

```
skyblessings-fastapi-pillow/
├── assets/              # 资源文件
│   ├── font/           # 字体文件
│   │   └── LXGWWenKaiMono-Medium.ttf
│   └── image/          # 图片资源
│       ├── background.png       # 遮罩图
│       ├── background0-5.png    # 装饰背景
│       └── text0-4.png          # 签文图片
├── src/                # 源代码
│   ├── main.py         # FastAPI 主应用
│   ├── render.py       # 图片渲染逻辑
│   └── draw_data.py    # 祝福数据
├── venv/               # Python 虚拟环境
├── config.toml         # 配置文件
└── README.md           # 说明文档
```

## API 端点

### GET /

返回 API 信息

**响应示例**:
```json
{
  "name": "祈福签 API",
  "version": "1.0.0",
  "endpoints": {
    "/": "API 信息",
    "/blessing": "获取随机祈福签图片（PNG）"
  }
}
```

### GET /blessing

生成并返回随机祈福签图片

**响应类型**: `image/png`

**调试输出**（log_level=debug 时）:
```
--- 抽签结果 (Debug) ---
背景图: background1.png
签文图: text0.png
结缘物：飞鸟
缘彩：蔚蓝 (#28d1e9)
祝福语: 互相在意的人，不会走散。
忌：不思进取
--------------------------
```

## 配置说明

### [server]

- `host`: 监听地址（默认 `0.0.0.0`）
- `port`: 监听端口（默认 `51205`）
- `log_level`: 日志级别（`info` 或 `debug`）

### [image]

- `width`: 图片宽度（默认 `1240`）
- `height`: 图片高度（默认 `620`）
- `font_size`: 字体大小（默认 `40`）
- `assets_dir`: 资源文件夹路径

## 性能

- **响应时间**: 约 50-150ms
- **内存占用**: 约 100-200MB
- **并发支持**: FastAPI 异步处理

## 故障排查

### 字体加载失败

如果提示字体加载失败，检查：
1. `assets/font/LXGWWenKaiMono-Medium.ttf` 文件是否存在
2. `config.toml` 中 `assets_dir` 路径是否正确

### 图片渲染错误

如果生成的图片颜色不对：
1. 检查 `assets/image/` 目录下所有 PNG 文件是否完整
2. 查看日志中的错误信息

### 端口被占用

修改 `config.toml` 中的 `port` 值，或停止占用端口的进程：

```powershell
# 查找占用端口的进程
netstat -ano | findstr :51205 # Windows PowerShell
sudo lsof -i :51205 # Linux bash

# 结束进程
taskkill /PID <进程ID> /F # Windows PowerShell
sudo kill -9 <进程ID> # Linux bash
```

