# AI Executive Assistant — Setup Guide

simple and easy step
---

## Step 1 — `.env` file banao (config)

`backend/.env`

```env
# Google Gemini
GEMINI_API_KEY=apni_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash

# Database - PostgreSQL  URL
DATABASE_URL=
```


## Step 2 — Backend installation

```bash
cd backend
pip install -r requirements.txt
```

## Step 3 — run Backend  (port 8000)

```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```


---

## Step 4 — run frontend

```bash
cd frontend
npm install
npm run dev
```

---

## Step 5 — open in  Browser

```
http://localhost:3000/ai
```

---

