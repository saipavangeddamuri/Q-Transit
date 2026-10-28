# Deploying Q-TRANSIT to Render

This guide outlines how to deploy the **Q-TRANSIT** platform to [Render](https://render.com). All configuration files (`render.yaml`, `Dockerfile`, `.python-version`, `.gitignore`) have been preconfigured and tested.

---

## Architecture Overview

| Component | Render Service Type | Root Directory | Build Command | Start / Publish |
|---|---|---|---|---|
| **Backend API** (FastAPI) | **Web Service** (Python 3.11) | `q-transit/backend` | `pip install --upgrade pip && pip install -r requirements.txt` | `uvicorn main:app --host 0.0.0.0 --port $PORT` |
| **Frontend UI** (React + Vite) | **Static Site** | `q-transit/frontend` | `npm install && npm run build` | Publish: `dist` |

Both services run on Render's **Free Tier**.

---

## Step 1: Commit and Push Code to GitHub

Open your terminal in the project root and push all files to your GitHub repository:

```powershell
git add .
git commit -m "Configure Render deployment with render.yaml and Dockerfile"
git push -u origin main
```

*(If you haven't authenticated GitHub CLI or personal access token yet, sign in when prompted).*

---

## Step 2: Choose Your Deployment Method

### Method 1: Render Blueprint (Recommended — 1-Click Automated Setup)

The repository includes a ready-to-use [`render.yaml`](file:///c:/Users/ROSHAN/OneDrive/Documents/SAI%20pvan/render.yaml) blueprint specification that automatically configures both services and connects them together.

1. Go to [dashboard.render.com](https://dashboard.render.com/) and sign in with GitHub.
2. Click **New +** in the top navigation and select **Blueprint**.
3. Connect your repository: `saipavangeddamuri/Q-Transit`.
4. Render will read `render.yaml` and show:
   - **`q-transit-backend`** (Web Service, Python 3.11, Free)
   - **`q-transit-frontend`** (Static Site, Free)
5. Click **Apply**.
6. Render will build and deploy both services in parallel. Once completed:
   - Your backend will be live at: `https://q-transit-backend.onrender.com`
   - Your frontend will be live at: `https://q-transit-frontend.onrender.com`

---

### Method 2: Manual Dashboard Setup (If Not Using Blueprint)

If you prefer configuring services manually via the Render UI:

#### Part A: Deploy Backend Web Service
1. In Render Dashboard, click **New +** → **Web Service**.
2. Select repository `saipavangeddamuri/Q-Transit`.
3. Configure settings:
   - **Name**: `q-transit-backend`
   - **Region**: Choose the closest region (e.g. Frankfurt / Ohio / Singapore)
   - **Branch**: `main`
   - **Root Directory**: `q-transit/backend`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install --upgrade pip && pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: `Free`
4. Expand **Advanced** → **Add Environment Variable**:
   - `PYTHON_VERSION`: `3.11.9`
5. Click **Create Web Service**. Wait 2–3 minutes for deployment to finish.
6. Copy your backend service URL (e.g., `https://q-transit-backend-xxxx.onrender.com`).

#### Part B: Deploy Frontend Static Site
1. In Render Dashboard, click **New +** → **Static Site**.
2. Select repository `saipavangeddamuri/Q-Transit`.
3. Configure settings:
   - **Name**: `q-transit-frontend`
   - **Branch**: `main`
   - **Root Directory**: `q-transit/frontend`
   - **Build Command**: `npm install && npm run build`
   - **Publish Directory**: `dist`
4. Expand **Advanced** → **Add Environment Variable**:
   - `VITE_API_BASE`: `https://<your-backend-name>.onrender.com/api`  
     *(Replace `<your-backend-name>` with the actual URL from Part A).*
5. Add a **Redirect / Rewrite Rule**:
   - Under **Redirects/Rewrites**, click **Add Rule**.
   - **Source**: `/*`
   - **Destination**: `/index.html`
   - **Action**: `Rewrite`
6. Click **Create Static Site**.

---

### Method 3: Unified Docker Container (Single Service)

If you prefer running frontend and backend together inside a single free container:

1. In Render Dashboard, click **New +** → **Web Service**.
2. Select repository `saipavangeddamuri/Q-Transit`.
3. Set **Runtime** to `Docker`.
4. Leave Dockerfile path as `./Dockerfile`.
5. Click **Create Web Service**. Render will automatically build the multi-stage Docker image and launch the unified app.

---

## Verifying the Deployment

1. **Backend Health Check**:
   Visit `https://<your-backend-name>.onrender.com/api/health` in your browser.  
   Expected JSON response:
   ```json
   {
     "status": "healthy",
     "service": "Q-TRANSIT Backend",
     "problem_id": "UC-053",
     "team": "HYPERQUBITS"
   }
   ```
2. **Interactive Swagger API Docs**:
   Visit `https://<your-backend-name>.onrender.com/docs` to test endpoints via the FastAPI Swagger UI.
3. **Frontend Dashboard**:
   Open `https://<your-frontend-name>.onrender.com`.  
   - The top header will display **"Backend: Online"** (green badge).
   - Click **"Load Default Sample Datasets"** to verify data ingestion.
   - Run a simulation to view quantum candidate bitstrings, comparison metrics, and interactive Gantt charts.

---

## Important Render Free-Tier Notes

1. **Free Tier Inactivity Sleep**:
   Render's free web services automatically spin down after 15 minutes of inactivity. When a new request arrives, it may take 30–50 seconds to cold-start. This is standard behavior on Render's free tier.
2. **CORS Support**:
   The backend is configured with wildcard CORS (`allow_origins=["*"]`), allowing requests from any frontend domain on Render.
3. **CSV & Report Persistence**:
   Generated run outputs and downloadable audit CSV files are stored in the backend `runs/` directory during active sessions.
