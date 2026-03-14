from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
from api import metrics, token, users, terminal
import os
import asyncio
from dotenv import load_dotenv
from lib.resource_manager import ResourceManager
from lib.logger import log

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.metrics_stop_event = asyncio.Event()
    app.state.metrics_task = asyncio.create_task(
        metrics_collector_loop(app.state.metrics_stop_event)
    )
    yield
    if hasattr(app.state, "metrics_stop_event"):
        app.state.metrics_stop_event.set()
    if hasattr(app.state, "metrics_task"):
        await app.state.metrics_task

app = FastAPI(
    title="MyCloude API",
    description="API for remote system management and monitoring.",
    version="0.1.0",
    lifespan=lifespan,
)

load_dotenv()
logger = log()

app.include_router(terminal.router, prefix="/api")
app.include_router(metrics.router, prefix="/api")
app.include_router(token.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.mount("/static", StaticFiles(directory="static"), name="static")


async def metrics_collector_loop(stop_event: asyncio.Event):
    """background task to periodically collect and insert system metrics."""
    interval = int(os.getenv("METRICS_COLLECTION_INTERVAL_SECONDS", "5"))
    logger.info(f"metrics collector started, collecting every {interval}.0 sec")
    rm = ResourceManager()
    try:
        while not stop_event.is_set():
            rm.InsertDataIntoDatabase()
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=interval)
            except asyncio.TimeoutError:
                pass
    except Exception as e:
        logger.error(f"error in metrics collector: {e}")
    finally:
        rm.close()
        logger.info("metrics collector stopped")

@app.get("/", response_class=HTMLResponse)
def read_root():
    """serves the main index.html file."""
    with open(os.path.join("static", "index.html")) as f:
        return HTMLResponse(content=f.read(), status_code=200)
