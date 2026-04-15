# Backend - Job Finder

API FastAPI responsavel por autenticacao, upload de curriculo, favoritos, cache e recomendacao de vagas.

## O que existe aqui

- cadastro, login e reset de senha
- upload e download de curriculo
- agregacao e ranking de vagas
- favoritos por usuario
- cache de fontes externas
- suporte a `sqlite` e `supabase` como camada de armazenamento

## Tecnologias

- Python
- FastAPI
- Uvicorn
- SQLite
- Supabase Python client

## Requisitos

- Python 3.11+ recomendado
- `pip`
- ambiente virtual opcional, mas recomendado

## Instalar dependencias

```bash
pip install -r requirements.txt
```

## Configuracao

O projeto le variaveis de ambiente com `python-dotenv`.

Crie um arquivo `.env` em `backend/` com base no `.env.example`.

### Exemplo usando SQLite

```env
STORAGE_PROVIDER=sqlite
SQLITE_DB_PATH=database.db
```

### Exemplo .env completo

```env
USER_LOCATION=Brazil
KEYWORDS=laravel,react,api,backend,fullstack
CACHE_TTL_SECONDS=3600
CACHE_DIR=.cache
ADZUNA_APP_ID=seu_id
ADZUNA_APP_KEY=sua_key
JOOBLE_API_KEY=sua-chave-aqui
RAPIDAPI_KEY=sua-chave-aqui
RAPIDAPI_HOST=seu-host-aqui

STORAGE_PROVIDER=supabase
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_KEY=sua-service-role-key
SUPABASE_USERS_TABLE=users
SUPABASE_FAVORITES_TABLE=favorites
```

## Rodar a API

```bash
uvicorn src.api:app --reload
```

A API fica disponivel por padrao em:

```txt
http://127.0.0.1:8000
```

## Endpoints principais

- `POST /register`: cria usuario
- `POST /login`: autentica e retorna token
- `POST /reset-password`: altera senha
- `GET /profile`: retorna dados do usuario e analise do curriculo
- `GET /jobs`: lista vagas recomendadas com paginacao
- `POST /favorites`: adiciona ou remove favorito
- `GET /favorites`: lista favoritos do usuario
- `POST /upload`: envia curriculo em PDF
- `GET /download-resume`: baixa curriculo do usuario
- `GET /cache/status`: mostra estado do cache
- `DELETE /cache`: limpa cache

## Banco de dados

### SQLite

- e o modo padrao
- cria as tabelas automaticamente ao iniciar
- ideal para desenvolvimento local rapido

### Supabase

- habilitado via `STORAGE_PROVIDER=supabase`
- use o arquivo `supabase_schema.sql` para criar as tabelas necessarias
- a aplicacao usa a camada `src/infrastructure/storage.py` para alternar entre SQLite e Supabase

## Arquivos principais

- `src/api.py`: rotas da API
- `src/config.py`: leitura das configuracoes e variaveis de ambiente
- `src/infrastructure/storage.py`: abstracao de persistencia com SQLite e Supabase
- `src/infrastructure/job_aggregator.py`: agregacao das fontes de vagas
- `src/application/`: regras de autenticacao, matcher e score de IA

## Validacao rapida

Para verificar a sintaxe dos arquivos principais:

```bash
python3 -m py_compile src/api.py src/config.py src/infrastructure/storage.py
```

## Observacoes importantes

- o projeto atual ainda usa token JWT proprio no backend
- o modo Supabase implementado nesta etapa usa o Supabase como banco, nao o Supabase Auth
- os curriculos enviados sao salvos localmente em `uploads/`
