from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from asess.routes import user_routes

app = FastAPI()

# Allow cross-origin requests from the frontend (during development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (CSS, JS, images, etc.)
app.mount("/static", StaticFiles(directory="/app/frontend"), name="static")

@app.get("/", tags=["root"])
def read_root():
    return RedirectResponse(url="/static/index.html")

app.include_router(user_routes.router, prefix="/users", tags=["users"])