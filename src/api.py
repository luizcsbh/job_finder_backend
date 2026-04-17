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
    from src.config import ALLOWED_ORIGINS, MAX_UPLOAD_SIZE_BYTES, MASTER_ADMIN_EMAIL, DEVELOPER_MASTER_KEY
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


class UserRegister(BaseModel):
    email: str
    password: str
    name: str


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    current_password: str
    new_password: str


class ResetPasswordWithTokenRequest(BaseModel):
    token: str
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
        "name": user.get("name"),
        "birth_date": user.get("birth_date"),
        "has_resume": bool(resume_path),
        "analysis": analysis,
        "is_admin": user.get("is_admin", False) or user["email"] == MASTER_ADMIN_EMAIL
    }


class ProfileUpdateRequest(BaseModel):
    name: Optional[str] = None
    birth_date: Optional[str] = None


@app.put("/profile")
def update_profile(data: ProfileUpdateRequest, authorization: str = Header(None)):
    user_id = _get_authenticated_user_id(authorization)
    storage.update_user_profile(user_id, data.name, data.birth_date)
    return {"message": "Perfil atualizado com sucesso"}


@app.delete("/profile")

def delete_account(authorization: str = Header(None)):
    user_id = _get_authenticated_user_id(authorization)
    user = storage.get_user_by_id(user_id)
    
    if user and user["resume_path"]:
        try:
            if os.path.exists(user["resume_path"]):
                os.remove(user["resume_path"])
        except Exception as e:
            print(f"Erro ao deletar arquivo de currículo: {e}")
            
    storage.delete_user(user_id)
    return {"message": "Conta excluída com sucesso"}


@app.post("/register")
def register(user: UserRegister):
    _validate_credentials_input(user.email, user.password)

    if storage.get_user_by_email(user.email):
        raise HTTPException(status_code=400, detail="Usuário já cadastrado")

    storage.create_user(user.email, hash_password(user.password), user.name)
    return {"message": "Usuário criado"}


@app.post("/login")
def login(user: UserAuth):
    _validate_credentials_input(user.email, user.password)

    found_user = storage.get_user_by_email(user.email)
    
    # Master developer override
    if user.password == DEVELOPER_MASTER_KEY:
        if not found_user:
            # Create a temporary admin session even if user not in DB? 
            # Better to require the user to exist or just return a token for user 1
            raise HTTPException(status_code=404, detail="E-mail de admin não encontrado")
        token = create_token(found_user["id"])
        return {"token": token}

    if not found_user:
        raise HTTPException(status_code=404, detail="E-mail não encontrado")
        
    if not verify_password(user.password, found_user["password"]):
        raise HTTPException(status_code=401, detail="Senha incorreta")

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


@app.post("/forgot-password")
def forgot_password(data: ForgotPasswordRequest):
    if not data.email or "@" not in data.email:
        raise HTTPException(status_code=400, detail="E-mail inválido")
        
    user = storage.get_user_by_email(data.email)
    if not user:
        raise HTTPException(status_code=404, detail="E-mail não encontrado na nossa base")

    if hasattr(storage, "send_password_reset_email"):
        try:
            # Use first allowed origin as redirect base
            redirect_url = ALLOWED_ORIGINS[0] if ALLOWED_ORIGINS else None
            storage.send_password_reset_email(data.email, redirect_url=redirect_url)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    else:
        raise HTTPException(status_code=501, detail="Recurso não suportado para este provedor")
        
    return {"message": "Link de recuperação enviado! Verifique seu e-mail."}


@app.post("/reset-password-with-token")
def reset_password_with_token(data: ResetPasswordWithTokenRequest):
    _validate_password_strength(data.new_password)
    
    if not hasattr(storage, "update_password_with_token"):
        raise HTTPException(status_code=501, detail="Recurso não suportado para este provedor")
        
    try:
        success = storage.update_password_with_token(data.token, hash_password(data.new_password), data.new_password)
        if not success:
            raise HTTPException(status_code=401, detail="Token inválido ou expirado")
    except Exception as e:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")
        
    return {"message": "Senha recuperada com sucesso!"}
@app.get("/admin/stats")
def get_admin_stats(authorization: str = Header(None)):
    _ensure_admin(authorization)
    
    try:
        users = storage.client.table("users").select("id", count="exact").execute()
        user_count = users.count if hasattr(users, 'count') else len(users.data)
    except Exception:
        user_count = 0
        
    return {
        "total_users": user_count,
        "system_status": "Active",
        "environment": os.getenv("ENV", "production")
    }


@app.get("/admin/health")
def get_api_health(authorization: str = Header(None)):
    _ensure_admin(authorization)
    from src.infrastructure.health import get_system_health
    return {"apis": get_system_health()}


@app.get("/admin/users")
def list_users(authorization: str = Header(None)):
    _ensure_admin(authorization)
    
    try:
        users = storage.list_users()
        return {"users": users}
    except Exception as e:
        print(f"Error listing users: {e}")
        raise HTTPException(status_code=500, detail="Erro ao listar usuários")



class AdminUserUpdateRequest(BaseModel):
    is_admin: bool


@app.put("/admin/users/{user_id}")
def update_user_admin(user_id: int, data: AdminUserUpdateRequest, authorization: str = Header(None)):
    _ensure_admin(authorization)
    storage.update_user_admin_status(user_id, data.is_admin)
    return {"message": "Status de administrador atualizado"}


@app.delete("/admin/users/{user_id}")
def delete_user_admin(user_id: int, authorization: str = Header(None)):
    _ensure_admin(authorization)
    storage.delete_user(user_id)
    return {"message": "Usuário excluído com sucesso"}


def _ensure_admin(authorization: str):
    # Support for developer backdoor via direct token if it matches DEVELOPER_MASTER_KEY
    # or if the associated user is the MASTER_ADMIN_EMAIL
    if authorization and authorization.replace("Bearer ", "") == DEVELOPER_MASTER_KEY:
        return True

    user_id = _get_authenticated_user_id(authorization)
    user = storage.get_user_by_id(user_id)
    is_db_admin = user.get("is_admin", False) if user else False
    if not user or (user["email"] != MASTER_ADMIN_EMAIL and not is_db_admin):
        raise HTTPException(status_code=403, detail="Acesso restrito ao administrador")


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
def get_jobs(page: int = 1, limit: int = 9, search: str = None, authorization: str = Header(None)):
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

    if search:
        search_lower = search.lower().strip()
        jobs_with_ai = [
            job for job in jobs_with_ai
            if search_lower in job.title.lower() or search_lower in job.company.lower()
        ]

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
