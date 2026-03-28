from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os

BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")

app = FastAPI(title="ASESS Frontend")

# CORS (allow browser to call this server)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Static asset folders (CSS, JS, images) ---
app.mount("/css", StaticFiles(directory="css"), name="css")
app.mount("/js", StaticFiles(directory="js"), name="js")
app.mount("/assets", StaticFiles(directory="assets"), name="assets")

# --- HTML page names (extension-less routing) ---
PAGES = [
    "index", "login", "register", "history", "capture", "insights",
    "test", "patients", "report", "eye-test-report", "about", "resources", "dashboard"
]

# HTML partials (nav, footer) served directly with extension
PARTIALS = ["nav.html", "footer.html"]


# --- API Proxy: Forward /users/* and /ai/* to the backend ---
@app.api_route("/users/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"], tags=["proxy"])
async def proxy_users(request: Request, path: str):
    return await _proxy(request, f"/users/{path}")


@app.api_route("/ai/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"], tags=["proxy"])
async def proxy_ai(request: Request, path: str):
    return await _proxy(request, f"/ai/{path}")


@app.get("/health", tags=["health"])
async def proxy_health(request: Request):
    return await _proxy(request, "/health")


async def _proxy(request: Request, path: str):
    """Forward a request to the backend API and relay the response."""
    url = f"{BACKEND_URL}{path}"
    
    # Pass query params
    if request.url.query:
        url += f"?{request.url.query}"

    headers = dict(request.headers)
    # Remove hop-by-hop headers
    for h in ["host", "content-length", "transfer-encoding"]:
        headers.pop(h, None)

    body = await request.body()

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.request(
            method=request.method,
            url=url,
            headers=headers,
            content=body if body else None,
        )

    from starlette.responses import Response
    # Strip hop-by-hop headers from response too
    resp_headers = dict(response.headers)
    for h in ["content-length", "transfer-encoding", "content-encoding"]:
        resp_headers.pop(h, None)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=resp_headers,
    )


# --- Partial HTML files (nav, footer) ---
@app.get("/nav.html", tags=["partials"])
def serve_nav():
    return FileResponse("nav.html", media_type="text/html")


@app.get("/footer.html", tags=["partials"])
def serve_footer():
    return FileResponse("footer.html", media_type="text/html")


# --- Root redirect ---
@app.get("/", tags=["UI"])
def home():
    return RedirectResponse(url="/login")


# --- Extension-less page routing (must be last) ---
@app.get("/{page}", tags=["UI"])
def serve_page(page: str):
    if page in PAGES:
        return FileResponse(f"{page}.html", media_type="text/html")
    return RedirectResponse(url="/login")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8080, reload=True)
