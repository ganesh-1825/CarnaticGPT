# ☁️ CarnaticGPT Cloud Deployment Manual

This document outlines the step-by-step procedure to deploy **CarnaticGPT** on production cloud platforms (AWS EC2, Google Cloud Run, or Azure App Service).

---

## 🏗️ 1. Deployment via Docker Compose (Virtual Private Server - VPS)

The easiest way to launch CarnaticGPT on any virtual machine (AWS EC2, DigitalOcean Droplet, GCP Compute Engine) is by utilizing Nginx and Docker Compose.

### Step 1: Clone & Configure Env
1. Setup a clean folder in the server: `mkdir /var/www/carnatic-gpt && cd /var/www/carnatic-gpt`
2. Populate the project structures.
3. Configure your production `.env` variables:
   ```env
   PORT=8000
   DATABASE_URL=sqlite:///./backend/carnatic_gpt.db
   JWT_SECRET=YOUR_SECURE_RANDOM_LONG_SECRET_KEY
   EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2
   GEMINI_API_KEY=YOUR_PRODUCTION_API_KEY
   ```

### Step 2: Compile Frontend Assets
We compile Vite statically to feed static Nginx layers:
```bash
cd frontend
npm install
npm run build
```
This outputs a compiled static bundle under `frontend/dist/`.

### Step 3: Launch Containers
Run from the root of `CarnaticGPT/`:
```bash
docker-compose -f deployment/docker-compose.yml up -d --build
```
This spins up:
- **FastAPI container:** Listening internally at port `8000`.
- **Nginx container:** Binding port `80` (HTTP) externally, serving our built React app from `frontend/dist` and forwarding `/api/` calls dynamically to the backend container.

---

## 🔒 2. Enabling SSL Certificates (Let's Encrypt Certbot)
To secure your client playgrounds over HTTPS:
1. Install Certbot on host VPS:
   ```bash
   sudo apt update
   sudo apt install certbot python3-certbot-nginx
   ```
2. Run Certbot certificate generator:
   ```bash
   sudo certbot --nginx -d your-domain.com
   ```
This automatically updates Nginx hosts and mounts SSL endpoints seamlessly.
