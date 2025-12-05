"""
FastAPI 主应用
"""

import toml
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

from render import BlessingRenderer


# 加载配置
CONFIG_FILE = Path(__file__).parent.parent / "config.toml"

def load_config() -> dict:
    """加载配置文件"""
    if CONFIG_FILE.exists():
        return toml.load(CONFIG_FILE)
    else:
        # 生成默认配置
        default_config = {
            "server": {
                "host": "0.0.0.0",
                "port": 51205,
                "log_level": "info"
            },
            "image": {
                "width": 1240,
                "height": 620,
                "font_size": 40,
                "assets_dir": "./assets"
            }
        }
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            toml.dump(default_config, f)
        print(f"✓ 已生成默认配置文件: {CONFIG_FILE}")
        return default_config


config = load_config()

# 创建 FastAPI 应用
app = FastAPI(
    title="祈福签 API",
    description="随机生成祈福签图片的 API 服务",
    version="1.0.0"
)

# 添加 CORS 支持
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建渲染器实例
renderer = BlessingRenderer(config)

# 获取调试模式
debug_mode = config["server"].get("log_level", "info").lower() == "debug"


@app.get("/")
async def index():
    """根路径：返回 API 信息"""
    return JSONResponse({
        "name": "祈福签 API",
        "version": "1.0.0",
        "endpoints": {
            "/": "API 信息",
            "/blessing": "获取随机祈福签图片（PNG）",
            "/favicon.ico": "网站图标"
        }
    })


@app.get("/blessing")
async def get_blessing():
    """
    获取随机祈福签图片
    
    Returns:
        PNG 图片
    """
    try:
        image_bytes = renderer.generate_blessing_image(debug=debug_mode)
        return Response(content=image_bytes, media_type="image/png")
    except Exception as e:
        print(f"错误：生成图片失败 {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"error": f"生成图片失败: {str(e)}"}
        )


@app.get("/favicon.ico")
async def favicon():
    """返回网站图标"""
    favicon_path = Path(config["image"]["assets_dir"]) / "favicon.ico"
    if favicon_path.exists():
        return FileResponse(favicon_path)
    else:
        return Response(status_code=404)


if __name__ == "__main__":
    import uvicorn
    
    host = config["server"]["host"]
    port = config["server"]["port"]
    
    print(f"🚀 启动祈福签 API 服务...")
    print(f"📍 地址: http://{host}:{port}")
    print(f"📖 API 文档: http://{host}:{port}/docs")
    print(f"🐛 调试模式: {'开启' if debug_mode else '关闭'}")
    print()
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=False,
        log_level=config["server"].get("log_level", "info").lower()
    )
