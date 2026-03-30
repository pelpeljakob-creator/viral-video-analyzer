from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import analyze, results

app = FastAPI(title="Viral Video Analyzer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze.router)
app.include_router(results.router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
