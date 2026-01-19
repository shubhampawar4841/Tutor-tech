# Deployment Guide

## Recommended Setup

### Frontend (Next.js) → Vercel
### Backend (FastAPI) → Railway or Render

---

## Option 1: Deploy Backend on Railway (Recommended)

### Why Railway?
- ✅ Easy Python deployment
- ✅ No execution time limits
- ✅ Built-in environment variables
- ✅ Automatic HTTPS
- ✅ Free tier available

### Steps:

1. **Create Railway Account**
   - Go to https://railway.app
   - Sign up with GitHub

2. **Deploy Backend**
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository
   - Railway will auto-detect Python

3. **Configure Environment Variables**
   Add these in Railway dashboard:
   ```
   SUPABASE_URL=your_supabase_url
   SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
   SUPABASE_ANON_KEY=your_anon_key
   OPENAI_API_KEY=your_openai_key
   DATA_DIR=/tmp
   ```

4. **Configure Build Settings**
   - Root Directory: `backend`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - Or create `Procfile`:
     ```
     web: uvicorn main:app --host 0.0.0.0 --port $PORT
     ```

5. **Get Backend URL**
   - Railway will give you a URL like: `https://your-app.railway.app`
   - Update CORS in `backend/main.py` to include this URL

---

## Option 2: Deploy Backend on Render

### Steps:

1. **Create Render Account**
   - Go to https://render.com
   - Sign up

2. **Create New Web Service**
   - Connect your GitHub repo
   - Settings:
     - **Build Command**: `cd backend && pip install -r requirements.txt`
     - **Start Command**: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
     - **Environment**: Python 3

3. **Add Environment Variables** (same as Railway)

4. **Get Backend URL**
   - Render gives: `https://your-app.onrender.com`

---

## Deploy Frontend on Vercel

### Steps:

1. **Install Vercel CLI** (optional)
   ```bash
   npm i -g vercel
   ```

2. **Deploy via Vercel Dashboard**
   - Go to https://vercel.com
   - Click "Add New Project"
   - Import your GitHub repository
   - Configure:
     - **Framework Preset**: Next.js
     - **Root Directory**: `my-app`
     - **Build Command**: `npm run build` (or `cd my-app && npm run build`)
     - **Output Directory**: `.next`

3. **Add Environment Variables**
   ```
   NEXT_PUBLIC_API_URL=https://your-backend-url.railway.app
   ```

4. **Update API Client**
   - Make sure `my-app/src/lib/api.ts` uses `process.env.NEXT_PUBLIC_API_URL`

---

## Update CORS Settings

After deploying backend, update `backend/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://your-app.vercel.app",  # Add your Vercel URL
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Update Frontend API URL

Create `my-app/.env.production`:
```
NEXT_PUBLIC_API_URL=https://your-backend-url.railway.app
```

Or set it in Vercel dashboard as environment variable.

---

## Alternative: Deploy Both on Vercel

If you want to deploy backend on Vercel too:

1. **Convert FastAPI to Vercel Serverless Functions**
   - Create `api/` directory in `my-app/`
   - Convert routes to serverless functions
   - ⚠️ **Limitations**: 10s execution time (Hobby), 60s (Pro)
   - ⚠️ Document processing might timeout

2. **Better Approach**: Use Vercel for frontend, keep backend separate

---

## Quick Deploy Checklist

- [ ] Backend deployed on Railway/Render
- [ ] Environment variables set
- [ ] CORS updated with frontend URL
- [ ] Frontend deployed on Vercel
- [ ] `NEXT_PUBLIC_API_URL` set in Vercel
- [ ] Test API connection
- [ ] Test file uploads
- [ ] Test document processing

---

## Cost Estimate

**Free Tier:**
- Vercel: Free (Hobby plan)
- Railway: $5/month free credit
- Render: Free tier available
- Supabase: Free tier (500MB database)

**Total**: ~$0-5/month for small projects

---

## Troubleshooting

### Backend timeout errors
- Use Railway/Render instead of Vercel serverless
- Increase timeout settings if available

### CORS errors
- Check backend CORS settings
- Verify frontend URL is in allowed origins

### Environment variables not working
- Restart services after adding env vars
- Check variable names match exactly

### File uploads failing
- Check file size limits
- Verify Supabase storage is configured
- Check storage bucket permissions





