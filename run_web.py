#!/usr/bin/env python3
"""
启动Web服务器
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

if __name__ == "__main__":
    import uvicorn
    from src.web.api import app

    print("=" * 60)
    print("GNSS/IMU数据处理平台 Web服务")
    print("=" * 60)
    print("\n访问地址: http://localhost:9998/static/index.html")
    print("\nAPI文档: http://localhost:9998/docs")
    print("\n按 Ctrl+C 停止服务\n")

    uvicorn.run(app, host="0.0.0.0", port=9998, log_level="info")
