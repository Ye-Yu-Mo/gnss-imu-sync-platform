"""
Web API 后端（FastAPI）

提供文件上传、数据处理、结果查询等REST API接口。
"""
import logging
import uuid
from pathlib import Path
from typing import Optional, Dict, Any
import json
import asyncio
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from ..pipeline.data_pipeline import DataPipeline, PipelineConfig, PipelineResults

logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="GNSS/IMU数据处理平台",
    description="异步数据处理管线Web接口",
    version="1.0.0",
    # 使用国内CDN，避免被墙
    swagger_ui_parameters={
        "syntaxHighlight.theme": "obsidian",
    }
)

# 自定义Swagger UI使用国内CDN
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """使用国内CDN的Swagger UI"""
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        swagger_js_url="https://cdn.bootcdn.net/ajax/libs/swagger-ui/5.11.0/swagger-ui-bundle.min.js",
        swagger_css_url="https://cdn.bootcdn.net/ajax/libs/swagger-ui/5.11.0/swagger-ui.min.css",
    )

# CORS配置（允许跨域）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

# 工作目录
UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("output/web_results")
UPLOAD_DIR.mkdir(exist_ok=True, parents=True)
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

# 任务状态存储（生产环境应该用Redis/数据库）
jobs: Dict[str, Dict[str, Any]] = {}


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "GNSS/IMU数据处理平台API",
        "version": "1.0.0",
        "endpoints": {
            "upload": "/api/upload",
            "process": "/api/process",
            "status": "/api/status/{job_id}",
            "results": "/api/results/{job_id}",
            "plots": "/api/plots/{job_id}/{filename}"
        }
    }


@app.post("/api/upload")
async def upload_files(
    gnss_file: UploadFile = File(...),
    imu_file: UploadFile = File(...),
    result_file: Optional[UploadFile] = File(None)
):
    """
    上传数据文件

    返回：job_id 和上传的文件路径
    """
    job_id = str(uuid.uuid4())
    job_dir = UPLOAD_DIR / job_id
    job_dir.mkdir(exist_ok=True)

    # 保存文件
    gnss_path = job_dir / "gnss.dat"
    imu_path = job_dir / "imu.dat"

    with open(gnss_path, "wb") as f:
        content = await gnss_file.read()
        f.write(content)

    with open(imu_path, "wb") as f:
        content = await imu_file.read()
        f.write(content)

    result_path = None
    if result_file:
        result_path = job_dir / "result.dat"
        with open(result_path, "wb") as f:
            content = await result_file.read()
            f.write(content)

    # 记录任务
    jobs[job_id] = {
        "id": job_id,
        "status": "uploaded",
        "created_at": datetime.now().isoformat(),
        "files": {
            "gnss": str(gnss_path),
            "imu": str(imu_path),
            "result": str(result_path) if result_path else None
        }
    }

    logger.info(f"文件上传完成: job_id={job_id}")

    return {
        "job_id": job_id,
        "status": "uploaded",
        "message": "文件上传成功"
    }


@app.post("/api/process/{job_id}")
async def process_data(
    job_id: str,
    imu_frequency: float = Form(95.0),
    interpolation_method: str = Form("linear"),
    interpolation_frequency: float = Form(95.0),
    generate_plots: bool = Form(True)
):
    """
    执行数据处理管线

    参数:
        job_id: 任务ID
        imu_frequency: IMU采样频率
        interpolation_method: 插值方法（linear/spline）
        interpolation_frequency: 插值目标频率
        generate_plots: 是否生成图表
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]

    if job["status"] != "uploaded":
        raise HTTPException(status_code=400, detail=f"Invalid job status: {job['status']}")

    # 更新状态
    job["status"] = "processing"
    job["started_at"] = datetime.now().isoformat()

    # 异步执行管线
    asyncio.create_task(run_pipeline_async(
        job_id,
        job["files"],
        imu_frequency,
        interpolation_method,
        interpolation_frequency,
        generate_plots
    ))

    return {
        "job_id": job_id,
        "status": "processing",
        "message": "处理已开始"
    }


async def run_pipeline_async(
    job_id: str,
    files: Dict[str, str],
    imu_frequency: float,
    interpolation_method: str,
    interpolation_frequency: float,
    generate_plots: bool
):
    """异步执行管线"""
    try:
        job = jobs[job_id]
        output_dir = OUTPUT_DIR / job_id

        # 创建配置
        config = PipelineConfig(
            gnss_file=files["gnss"],
            imu_file=files["imu"],
            result_file=files.get("result"),
            output_dir=str(output_dir),
            imu_frequency=imu_frequency,
            interpolation_method=interpolation_method,
            interpolation_frequency=interpolation_frequency,
            generate_plots=generate_plots
        )

        # 执行管线
        pipeline = DataPipeline(config)
        results = pipeline.run()

        # 保存结果
        job["status"] = "completed"
        job["completed_at"] = datetime.now().isoformat()
        job["results"] = {
            "gnss_count": len(results.gnss_data),
            "imu_count": len(results.imu_data),
            "interpolated_count": len(results.interpolated_gnss) if results.interpolated_gnss else 0,
            "alignment_report": results.alignment_report,
            "output_dir": str(output_dir)
        }

        # 查找生成的图表
        plots_dir = output_dir / "plots"
        if plots_dir.exists():
            job["results"]["plots"] = [p.name for p in plots_dir.glob("*.png")]

        logger.info(f"管线执行完成: job_id={job_id}")

    except Exception as e:
        logger.error(f"管线执行失败: job_id={job_id}, error={e}")
        job["status"] = "failed"
        job["error"] = str(e)
        job["completed_at"] = datetime.now().isoformat()


@app.get("/api/status/{job_id}")
async def get_status(job_id: str):
    """查询任务状态"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    return jobs[job_id]


@app.get("/api/results/{job_id}")
async def get_results(job_id: str):
    """获取处理结果"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]

    if job["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Job not completed, current status: {job['status']}"
        )

    return {
        "job_id": job_id,
        "status": job["status"],
        "results": job.get("results", {})
    }


@app.get("/api/plots/{job_id}/{filename}")
async def get_plot(job_id: str, filename: str):
    """获取图表文件"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]

    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job not completed")

    plot_path = OUTPUT_DIR / job_id / "plots" / filename

    if not plot_path.exists():
        raise HTTPException(status_code=404, detail="Plot not found")

    return FileResponse(plot_path)


@app.get("/api/jobs")
async def list_jobs():
    """列出所有任务"""
    return {
        "jobs": [
            {
                "id": job_id,
                "status": job["status"],
                "created_at": job.get("created_at")
            }
            for job_id, job in jobs.items()
        ]
    }


@app.delete("/api/jobs/{job_id}")
async def delete_job(job_id: str):
    """删除任务（清理文件）"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    # 删除文件
    import shutil
    job_dir = UPLOAD_DIR / job_id
    output_dir = OUTPUT_DIR / job_id

    if job_dir.exists():
        shutil.rmtree(job_dir)
    if output_dir.exists():
        shutil.rmtree(output_dir)

    # 删除记录
    del jobs[job_id]

    return {"message": "Job deleted"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
