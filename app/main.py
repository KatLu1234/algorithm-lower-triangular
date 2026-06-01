from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

from app.api.api import api_router
from app.api.endpoints.auth import _AuthError

app = FastAPI(
    title="Lower Triangular Project API",
    openapi_url="/api/v1/openapi.json"
)

# 개발 환경: nginx 프록시 경유 시 같은 오리진이라 CORS 불필요하지만,
# Vite 직접 호출(5173 → 8000) 디버그 흐름을 위해 와일드카드 허용.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.exception_handler(RequestValidationError)
async def _validation_exception_handler(_request: Request, exc: RequestValidationError):
    """frontend 계약 ({detail, code}) 에 맞춰 Pydantic 검증 에러 정형화.

    base/architecture.md §5.1: 에러 응답은 사람이 읽을 수 있는 detail + 분기용 code.
    """
    errs = exc.errors()
    if errs:
        first = errs[0]
        loc = ".".join(str(p) for p in first.get("loc", []) if p != "body")
        msg = first.get("msg", "validation error")
        detail = f"{loc}: {msg}" if loc else msg
    else:
        detail = "요청 형식이 올바르지 않습니다."
    return JSONResponse(
        status_code=422,
        content={"detail": detail, "code": "VALIDATION_ERROR"},
    )


@app.exception_handler(_AuthError)
async def _auth_exception_handler(_request: Request, exc: _AuthError):
    """auth Depends 내부에서 던진 인증 실패를 {detail, code} 표준으로 변환."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "code": exc.code},
    )


@app.get("/")
def root():
    return {"message": "Welcome to Lower Triangular Project API"}


@app.get("/healthz")
def healthz():
    return {"status": "ok"}
