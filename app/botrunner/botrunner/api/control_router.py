from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.post("/pipeline/start")
async def start_pipeline():
    from ..pipeline.capture_loop import pipeline_manager
    if pipeline_manager.is_running():
        raise HTTPException(status_code=409, detail="Pipeline already running")
    await pipeline_manager.start()
    return {"message": "Pipeline started"}


@router.post("/pipeline/stop")
async def stop_pipeline():
    from ..pipeline.capture_loop import pipeline_manager
    if not pipeline_manager.is_running():
        raise HTTPException(status_code=409, detail="Pipeline not running")
    await pipeline_manager.stop()
    return {"message": "Pipeline stopped"}


@router.get("/pipeline/status")
async def pipeline_status():
    from ..pipeline.capture_loop import pipeline_manager
    return pipeline_manager.get_status()
