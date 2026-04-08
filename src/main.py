"""
FastAPI 主应用
"""

import toml
import traceback
from pathlib import Path
from typing import Optional

import hashlib
import base64
from fastapi import FastAPI, Response, Query
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
                "log_level": "info",
                "hide_error_details": False,
                "max_seed_param_length": 500
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
        print(f"\033[91m[WARN] 未检测到配置文件，已自动生成默认配置：{CONFIG_FILE.resolve()}\033[0m")
        return default_config


config = load_config()

# 创建 FastAPI 应用
app = FastAPI(
    title="Sky光遇祈福签 API",
    description="随机生成光遇祈福签图片的 API 服务",
    version="0.2.3"
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
hide_error_details = config["server"].get("hide_error_details", False)
max_seed_param_length = config["server"].get("max_seed_param_length", 500)


@app.get("/")
async def index():
    """根路径：返回 API 信息"""
    return JSONResponse({
        "title": app.title,
        "description": app.description,
        "version": app.version,
        "endpoints": {
            "/": "API 信息",
            "/blessing": {
                "description": "获取随机祈福签图片",
                "params": {
                    "type": "响应格式：image（默认，PNG图片）| json（含图片base64）| json_without_image",
                    "a/b/c/d/e": "可选种子参数，相同组合返回相同结果（如 ?a=玩家名&b=日期）",
                }
            },
            "/favicon.ico": "网站图标"
        }
    })


@app.get("/blessing")
async def get_blessing(
    type: str = Query(default="image", pattern="^(image|json|json_without_image)$"),
    a: Optional[str] = None,
    b: Optional[str] = None,
    c: Optional[str] = None,
    d: Optional[str] = None,
    e: Optional[str] = None,
):
    try:
        seed = None
        if any(v is not None for v in (a, b, c, d, e)):
            if any(v and len(v) > max_seed_param_length for v in (a, b, c, d, e)):
                return JSONResponse(status_code=400, content={"error": "参数过长"})
            raw = "|".join(v or "" for v in (a, b, c, d, e))
            seed = int(hashlib.md5(raw.encode()).hexdigest(), 16)

        result = renderer.perform_draw(seed=seed)
        if type == "image":
            image_bytes = renderer.generate_blessing_image_from_result(result, debug=debug_mode)
            return Response(content=image_bytes, media_type="image/png")

        data = {
            "fortune_level": result.fortune_level,
            "background_id": result.background_id,
            "dordas": result.dordas,
            "blessing": result.blessing,
            "entry": result.entry,
            "dordas_color": result.dordas_color,
            "color_hex": result.color_hex,
        }
        if type == "json":
            image_bytes = renderer.generate_blessing_image_from_result(result, debug=debug_mode)
            data["image_base64"] = base64.b64encode(image_bytes).decode("utf-8")
        return JSONResponse(data)
    except Exception as e:
        traceback.print_exc()
        error_msg = "内部服务器错误" if hide_error_details else str(e)
        return JSONResponse(status_code=500, content={"error": error_msg})


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
    print(f"📍 跟路由: http://{host}:{port}")
    print(f"📖 API 文档: http://{host}:{port}/docs")
    print(f"🔖 抽签图片: http://{host}:{port}/blessing")
    print(f"🐛 调试模式: {'开启' if debug_mode else '关闭'}")
    print()
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=False,
        log_level=config["server"].get("log_level", "info").lower()
    )
