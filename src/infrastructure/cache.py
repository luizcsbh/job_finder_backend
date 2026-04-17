"""
Cache em duas camadas para as chamadas às APIs de vagas:
  - Camada 1: in-memory (instantâneo, dura até o servidor reiniciar)
  - Camada 2: arquivo JSON em disco (persiste entre reinícios)

Configuração via .env:
  CACHE_TTL_SECONDS  — tempo de vida do cache em segundos (padrão: 3600 = 1h)
  CACHE_DIR          — pasta onde os arquivos JSON ficam (padrão: .cache)

Uso direto:
    from src.infrastructure.cache import cached

    @cached("nome_da_fonte")
    def fetch_jobs_minha_api() -> list[Job]:
        ...
"""
import json
import os
import time
import threading
from functools import wraps
from typing import Callable

# Importação lazy para evitar circular import
def _make_job(d: dict):
    from src.domain.job import Job
    j = Job(
        title=d.get("title", ""),
        company=d.get("company", ""),
        location=d.get("location", ""),
        description=d.get("description", ""),
        url=d.get("url", ""),
        source=d.get("source", ""),
        datate_posted=d.get("datate_posted", ""),
        category=d.get("category", []),
        salary=d.get("salary", ""),
    )
    j.score    = d.get("score", 0)
    j.ai_score = d.get("ai_score", 0)
    return j


def _job_to_dict(job) -> dict:
    return {
        "title":       job.title,
        "company":     job.company,
        "location":    job.location,
        "description": job.description,
        "url":         job.url,
        "source":      job.source,
        "score":       getattr(job, "score", 0),
        "ai_score":    getattr(job, "ai_score", 0),
        "datate_posted": getattr(job, "datate_posted", ""),
        "category":    getattr(job, "category", []),
        "salary":      getattr(job, "salary", ""),
    }


# ── Configuração ─────────────────────────────────────────────────────────────
CACHE_TTL = int(os.getenv("CACHE_TTL_SECONDS", "3600"))   # 1 hora padrão
CACHE_DIR = os.getenv("CACHE_DIR", ".cache")
os.makedirs(CACHE_DIR, exist_ok=True)

# ── Armazenamento in-memory ──────────────────────────────────────────────────
_store: dict[str, dict] = {}
_lock  = threading.Lock()


# ── Helpers internos ─────────────────────────────────────────────────────────

def _cache_path(key: str) -> str:
    safe = key.replace("/", "_").replace(" ", "_")
    return os.path.join(CACHE_DIR, f"{safe}.json")


def _is_fresh(ts: float) -> bool:
    return (time.time() - ts) < CACHE_TTL


def _load_from_disk(key: str):
    path = _cache_path(key)
    try:
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            entry = json.load(f)
        if _is_fresh(entry.get("ts", 0)):
            jobs = [_make_job(d) for d in entry["data"]]
            return jobs
    except Exception as e:
        print(f"[Cache] Erro ao ler disco para '{key}': {e}")
    return None


def _save_to_disk(key: str, jobs: list) -> None:
    path = _cache_path(key)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(
                {"ts": time.time(), "data": [_job_to_dict(j) for j in jobs]},
                f,
                ensure_ascii=False,
                indent=2,
            )
    except Exception as e:
        print(f"[Cache] Erro ao salvar disco para '{key}': {e}")


# ── API pública ───────────────────────────────────────────────────────────────

def get(key: str):
    """Retorna lista de Jobs do cache (in-memory ou disco) se ainda válido."""
    with _lock:
        entry = _store.get(key)
        if entry and _is_fresh(entry["ts"]):
            age = int(time.time() - entry["ts"])
            print(f"[Cache] ✅ HIT memory '{key}' ({age}s atrás, expira em {CACHE_TTL - age}s)")
            return entry["jobs"]

    data = _load_from_disk(key)
    if data is not None:
        with _lock:
            _store[key] = {"jobs": data, "ts": time.time()}
        print(f"[Cache] 💾 HIT disco '{key}' — {len(data)} vagas")
        return data

    print(f"[Cache] ❌ MISS '{key}'")
    return None


def set_cache(key: str, jobs: list) -> None:
    """Armazena lista de Jobs no cache in-memory e em disco."""
    with _lock:
        _store[key] = {"jobs": jobs, "ts": time.time()}
    _save_to_disk(key, jobs)
    print(f"[Cache] 💾 SET '{key}' — {len(jobs)} vagas | TTL: {CACHE_TTL}s")


def invalidate(key: str | None = None) -> None:
    """Invalida uma chave específica ou todo o cache."""
    with _lock:
        if key:
            _store.pop(key, None)
        else:
            _store.clear()

    if key:
        path = _cache_path(key)
        if os.path.exists(path):
            os.remove(path)
        print(f"[Cache] 🗑️  Invalidado: '{key}'")
    else:
        for fname in os.listdir(CACHE_DIR):
            if fname.endswith(".json"):
                os.remove(os.path.join(CACHE_DIR, fname))
        print("[Cache] 🗑️  Cache completo invalidado.")


def status() -> dict:
    """Retorna o estado atual de cada chave no cache."""
    with _lock:
        result = {}
        for key, entry in _store.items():
            age       = int(time.time() - entry["ts"])
            remaining = max(0, CACHE_TTL - age)
            result[key] = {
                "items":         len(entry["jobs"]),
                "age_seconds":   age,
                "ttl_remaining": remaining,
                "fresh":         remaining > 0,
            }
    return result


# ── Decorator ─────────────────────────────────────────────────────────────────

def cached(key: str):
    """
    Decorator que adiciona cache automático a funções que retornem list[Job].

    Exemplo:
        @cached("remotive")
        def fetch_jobs() -> list[Job]:
            ...
    """
    def decorator(fn: Callable):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            hit = get(key)
            if hit is not None:
                return hit
            result = fn(*args, **kwargs)
            if result:
                set_cache(key, result)
            return result
        return wrapper
    return decorator
