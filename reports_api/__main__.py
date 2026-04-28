#!/usr/bin/env python3
import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from reports_api.common.globals import GlobalsSingleton
from reports_api.database.db_manager import init_db_manager
from reports_api.database.session import init_db, shutdown_db
from reports_api.response_code.analytics_exception import AnalyticsException
from reports_api.routers import (
    calendar,
    facility_ports,
    hosts,
    links,
    projects,
    sites,
    slices,
    slivers,
    users,
    version,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.getLogger("sqlalchemy.engine.Engine").setLevel(logging.WARNING)
    globals_ = GlobalsSingleton.get()
    init_db(globals_.config)
    init_db_manager(globals_.log)
    yield
    await shutdown_db()


app = FastAPI(title="Reports API", version="1.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in [
    version.router,
    sites.router,
    hosts.router,
    projects.router,
    users.router,
    slices.router,
    slivers.router,
    calendar.router,
    links.router,
    facility_ports.router,
]:
    app.include_router(router)


@app.exception_handler(AnalyticsException)
async def analytics_exception_handler(request: Request, exc: AnalyticsException):
    return JSONResponse(
        status_code=exc.http_error_code,
        content={"errors": [{"details": str(exc)}]},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"errors": [{"details": f"Internal server error: {exc}"}]},
    )


if __name__ == "__main__":
    uvicorn.run("reports_api.__main__:app", host="0.0.0.0", port=8080, workers=4)
