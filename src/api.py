import math
import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from jwt import InvalidTokenError
from pydantic import BaseModel

try:
    from src.application.ai_matcher import calculate_ai_scores
    from src.application.auth import create_token, decode_token, hash_password, verify_password
    from src.application.matcher import rank_jobs
    from src.config import ALLOWED_ORIGINS, MAX_UPLOAD_SIZE_BYTES
    from src.infrastructure import cache as job_cache
    from src.infrastructure.job_aggregator import fetch_all_jobs
    from src.infrastructure.resume_parser import determine_career_info, extract_text_from_pdf
    from src.infrastructure.storage import get_storage
except ImportError:
    from application.ai_matcher import calculate_ai_scores
    from application.auth import create_token, decode_token, hash_password, verify_password
    from matcher import rank_jobs
    from config import ALLOWED_ORIGINS, MAX_UPLOAD_SIZE_BYTES
    from infrastructure import cache as job_cache
    from infrastructure.job_aggregator import fetch_all_jobs
    from infrastructure.resume_parser import determine_career_info, extract_text_from_pdf
    from infrastructure.storage import get_storage

app = FastAPI(title="Job Finder API")
storage = get_storage()

# CORS configuration
# In production, ALLOWED_ORIGINS should contain the Netlify URL
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS if ALLOWED_ORIGINS else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok", "environment": os.getenv("ENV", "development")}

UPLOAD_DIR = "uploads"
Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)


class UserAuth(BaseModel):
    email: str
    password: str


class ResetPasswordRequest(BaseModel):
    current_password: str
    new_password: str


class FavoriteRequest(BaseModel):
    job_url: str


@app.get("/profile")
def get_user_profile(authorization: str = Header(None)):
    user_id = _get_authenticated_user_id(authorization)
    user = storage.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    resume_path = user["resume_path"]
    analysis = {}
    if resume_path:
        text = extract_text_from_pdf(resume_path)
        analysis = determine_career_info(text)

    return {
        "email": user["email"],
        "has_resume": bool(resume_path),
        "analysis": analysis,
    }


@app.post("/register")
def register(user: UserAuth):
    _validate_credentials_input(user.email, user.password)

    if storage.get_user_by_email(user.email):
        raise HTTPException(status_code=400, detail="Usuário já cadastrado")

    storage.create_user(user.email, hash_password(user.password))
    return {"message": "Usuário criado"}


@app.post("/login")
def login(user: UserAuth):
    _validate_credentials_input(user.email, user.password)

    found_user = storage.get_user_by_email(user.email)
    if not found_user or not verify_password(user.password, found_user["password"]):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    token = create_token(found_user["id"])
    return {"token": token}


@app.post("/reset-password")
def reset_password(data: ResetPasswordRequest, authorization: str = Header(None)):
    _validate_password_strength(data.new_password)

    user_id = _get_authenticated_user_id(authorization)
    user = storage.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    if not verify_password(data.current_password, user["password"]):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    storage.update_user_password(user["email"], hash_password(data.new_password))
    return {"message": "Senha alterada com sucesso"}


@app.get("/cache/status")
def get_cache_status(authorization: str = Header(None)):
    _get_authenticated_user_id(authorization)
    return {"cache": job_cache.status(), "ttl_seconds": job_cache.CACHE_TTL}


@app.delete("/cache")
def clear_cache(source: str = None, authorization: str = Header(None)):
    _get_authenticated_user_id(authorization)
    job_cache.invalidate(source)
    msg = f"Cache '{source}' invalidado" if source else "Cache completo invalidado"
    return {"message": msg}


@app.get("/jobs")
def get_jobs(page: int = 1, limit: int = 9, authorization: str = Header(None)):
    if page < 1 or limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="Parâmetros de paginação inválidos")

    user_id = _get_authenticated_user_id(authorization)
    user = storage.get_user_by_id(user_id)

    if not user or not user["resume_path"]:
        return {
            "error": "RESUME_REQUIRED",
            "message": "Você precisa enviar seu currículo no Dashboard antes de buscar vagas.",
        }

    resume_path = user["resume_path"]
    jobs = fetch_all_jobs()
    ranked = rank_jobs(jobs)

    try:
        resume_text = extract_text_from_pdf(resume_path)
        jobs_with_ai = calculate_ai_scores(resume_text, ranked)
    except Exception:
        jobs_with_ai = [job for job in ranked]
        for job in jobs_with_ai:
            job.ai_score = 0

    start = (page - 1) * limit
    end = start + limit
    paginated = jobs_with_ai[start:end]
    total_pages = max(1, math.ceil(len(jobs_with_ai) / limit))

    return {
        "page": page,
        "total": len(jobs_with_ai),
        "totalPages": total_pages,
        "jobs": [
            {
                "title": job.title,
                "company": job.company,
                "score": job.score,
                "ai_score": getattr(job, "ai_score", 0),
                "source": job.source,
                "url": job.url,
            }
            for job in paginated
        ],
    }


@app.post("/favorites")
def toggle_favorite(data: FavoriteRequest, authorization: str = Header(None)):
    user_id = _get_authenticated_user_id(authorization)

    favorited = storage.toggle_favorite(user_id, data.job_url)
    if not favorited:
        return {"message": "Removido dos favoritos", "favorited": False}

    return {"message": "Adicionado aos favoritos", "favorited": True}


@app.get("/favorites")
def get_favorites(authorization: str = Header(None)):
    user_id = _get_authenticated_user_id(authorization)
    fav_urls = storage.get_favorite_urls(user_id)

    all_jobs = fetch_all_jobs()
    favorites_list = [
        {
            "title": job.title,
            "company": job.company,
            "score": job.score,
            "ai_score": getattr(job, "ai_score", 0),
            "source": job.source,
            "url": job.url,
        }
        for job in all_jobs
        if job.url in fav_urls
    ]
    return {"favorites": favorites_list}


@app.post("/upload")
def upload_resume(file: UploadFile = File(...), authorization: str = Header(None)):
    user_id = _get_authenticated_user_id(authorization)
    file_path = _store_uploaded_resume(user_id, file)
    storage.update_user_resume_path(user_id, file_path)
    return {"message": "Currículo enviado e vinculado ao seu perfil"}


@app.get("/download-resume")
def download_resume(authorization: str = Header(None)):
    user_id = _get_authenticated_user_id(authorization)
    user = storage.get_user_by_id(user_id)

    if not user or not user["resume_path"]:
        raise HTTPException(status_code=404, detail="Nenhum currículo encontrado para este usuário")

    file_path = _validate_stored_resume_path(user["resume_path"])
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Arquivo não encontrado no servidor")

    filename = os.path.basename(file_path)
    return FileResponse(path=file_path, media_type="application/pdf", filename=filename)



def _get_authenticated_user_id(authorization: Optional[str]) -> int:
    if not authorization:
        raise HTTPException(status_code=401, detail="Não autorizado")

    try:
        scheme, token = authorization.split(" ", 1)
        if scheme.lower() != "bearer":
            raise ValueError("invalid auth scheme")
        decoded = decode_token(token)
        return int(decoded["user_id"])
    except (ValueError, KeyError, InvalidTokenError):
        raise HTTPException(status_code=401, detail="Token inválido")



def _validate_credentials_input(email: str, password: str):
    if not email or "@" not in email or len(email) > 254:
        raise HTTPException(status_code=400, detail="Email inválido")

    _validate_password_strength(password)



def _validate_password_strength(password: str):
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="A senha deve ter pelo menos 8 caracteres")



def _store_uploaded_resume(user_id: int, file: UploadFile) -> str:
    original_name = os.path.basename(file.filename or "")
    extension = Path(original_name).suffix.lower()
    if extension != ".pdf" or file.content_type not in {"application/pdf", "application/octet-stream"}:
        raise HTTPException(status_code=400, detail="Apenas arquivos PDF são permitidos")

    content = file.file.read(MAX_UPLOAD_SIZE_BYTES + 1)
    if len(content) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="Arquivo excede o tamanho máximo permitido")

    upload_dir = Path(UPLOAD_DIR).resolve()
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / f"{user_id}_resume.pdf"
    with open(file_path, "wb") as destination:
        destination.write(content)

    return str(file_path)



def _validate_stored_resume_path(file_path: str) -> str:
    resolved_path = Path(file_path).resolve()
    upload_dir = Path(UPLOAD_DIR).resolve()
    if upload_dir not in resolved_path.parents:
        raise HTTPException(status_code=404, detail="Arquivo não encontrado no servidor")
    return str(resolved_path)
