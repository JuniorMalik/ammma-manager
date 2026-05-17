# 🌍 Guia de Deploy — AMMMA 3D Manager

**Domínio**: `https://ammma3d.com/`

Arquitetura híbrida: o **Frontend** (HTML/CSS/JS) fica na Hostinger em `ammma3d.com`, e o **Backend** (Python/FastAPI) fica em um serviço especializado como Railway ou Render.

---

## 🏗️ Passo 1: Backend — Railway ou Render

Escolha um:
- **Railway.app** ← Recomendado (simples, barato, sem cold start problemático)
- **Render.com** ← Alternativa gratuita (tem cold start de ~30s no plano free)

### Como fazer o deploy:
1. Crie uma conta e suba **apenas a pasta `backend`** via GitHub ou upload direto.
2. Defina o comando de start:
   ```
   uvicorn main:app --host 0.0.0.0 --port $PORT
   ```
3. Após o deploy, o Railway/Render dará uma URL pública, ex:
   ```
   https://ammma-api.up.railway.app
   ```
4. **Copie essa URL** — você vai precisar dela no próximo passo.

---

## 🎨 Passo 2: Configurar o Frontend com a URL do Backend

Abra **dois** arquivos e substitua a URL:

### `frontend/app.js` — linha 7:
```javascript
// ANTES:
const API_BASE_URL = '';

// DEPOIS (coloque a URL real do Railway/Render):
const API_BASE_URL = 'https://ammma-api.up.railway.app';
```

### `frontend/login.html` — linha 75:
```javascript
// ANTES:
const API_BASE_URL = '';

// DEPOIS (mesma URL):
const API_BASE_URL = 'https://ammma-api.up.railway.app';
```

---

## ☁️ Passo 3: Subir o Frontend na Hostinger

1. Acesse o painel da Hostinger → **Gerenciador de Arquivos**.
2. Abra a pasta `public_html` (que corresponde a `ammma3d.com`).
3. **Delete tudo** que estiver lá (se houver algo padrão).
4. Suba **o conteúdo** da pasta `frontend` diretamente para `public_html`:
   - `index.html` deve ficar em `public_html/index.html` (raiz)
   - `login.html`, `app.js`, `style.css`, `sw.js`, `manifest.json` idem
   - Pasta `logo/` → `public_html/logo/`
5. Pronto. Acesse `https://ammma3d.com` para testar.

---

## 🔐 Passo 4: Banco de Dados e Uploads

- O banco `database.db` fica no servidor do **backend** (Railway/Render), na pasta `data/`.
- Os uploads de imagens (galeria) ficam na pasta `backend/uploads/` do servidor backend.
- O logo para PDF: pasta `frontend/logo/` no servidor backend.

> **Importante**: Configure variáveis de ambiente no Railway/Render se necessário (ex: SECRET_KEY para JWT).

---

## ✅ Resultado Final

| URL | O que serve |
|---|---|
| `https://ammma3d.com` | Frontend (Hostinger) — Login, Dashboard, Kanban, etc |
| `https://ammma-api.up.railway.app` | Backend (Railway) — API, banco de dados, PDFs |

O frontend em `ammma3d.com` se comunica com o backend no Railway para buscar e salvar dados. O usuário final só vê `ammma3d.com`.
