# CivicAI Vercel Deployment Guide 🚀

The project is fully prepped for immediate Vercel hosting!

---

## 📁 Pre-configured Files Created

The repository now contains all necessary Vercel configuration files:

1. `vercel.json` (Root configuration - routes frontend build & FastAPI serverless function rewrites)
2. `api/index.py` (Vercel Python Serverless Function entrypoint wrapping FastAPI `backend.app.main:app`)
3. `package.json` (Root npm package defining standard Vercel build script `cd frontend && npm install && npm run build`)
4. `requirements.txt` (Root Python dependencies for Vercel serverless runtime)
5. `frontend/vercel.json` (Fallback config for standalone frontend deployment)

---

## ⚡ Option 1: Deploy via Vercel CLI (Fastest)

Run the following command in the project root directory:

```bash
npx vercel
```

Follow the interactive prompts:
* **Set up and deploy?**: `y`
* **Which scope?**: Choose your Vercel account
* **Link to existing project?**: `n`
* **Project name**: `civicai` (or your preferred name)
* **In which directory is your code located?**: `./`

To deploy to production:

```bash
npx vercel --prod
```

---

## 🌐 Option 2: Deploy via Vercel Web Dashboard (GitHub / Git)

1. Push your repository to GitHub / GitLab / Bitbucket.
2. Go to [Vercel Dashboard](https://vercel.com/new).
3. Import your **CivicAI** repository.
4. Vercel will automatically detect the settings from `vercel.json`:
   - **Framework Preset**: Vite / Other
   - **Build Command**: `cd frontend && npm install && npm run build`
   - **Output Directory**: `frontend/dist/public`
5. Click **Deploy**.

---

## ⚙️ Environment Variables (Vercel Dashboard Settings)

In your Vercel Project Settings under **Environment Variables**, add:

| Key | Description / Example Value |
|---|---|
| `VITE_API_BASE_URL` | Set to your Vercel app URL (e.g. `https://civicai.vercel.app`) or leave empty for relative `/api/v1` routing. |
| `RAG_SERVICE_URL` | URL of your deployed RAG microservice (e.g. `http://127.0.0.1:8001` or Render/Railway hosted URL). |
| `GEMINI_API_KEY` | Your Gemini API Key for legal AI generation. |

---

## ✨ Features Included on Vercel Live Deployment

- **Full React Assistant UI**: Action-oriented civic guidance cards, source citations, and 1-click test buttons.
- **FastAPI Serverless API**: Serves `/api/v1/query`, `/api/v1/rti/draft`, `/api/v1/health`, etc.
- **RTI Drafting Agent**: Formal application generation under the Right to Information Act, 2005.
