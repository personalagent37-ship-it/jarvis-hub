# 🚀 JARVIS 24/7 Production Deployment Guide

This guide details how to deploy your JARVIS ecosystem for **100% Free 24/7 Operation** by separating the Frontend (Netlify) and Backend (Oracle Cloud OCI).

---

## 📁 Architecture & Folder Structure

We have differentiated the project into two distinct deployment targets:

* **UI / Frontend (`jarvis_hub/public/` + `netlify.toml`):**
  * Contains your interactive HTML5/CSS/React dashboard, sounds, videos, and 3D robot animations.
  * Deployed automatically to **Netlify** (Global CDN).
* **AI Engine / Backend (`/home/talha/Desktop/jartvis/`):**
  * Contains `whatsapp_server.py`, `brain.py`, OpenRouter AI tools, and Node.js Puppeteer (`hub.js`).
  * Deployed to **Oracle Cloud Infrastructure (OCI)** Linux Virtual Machine.

---

## 🌐 Step 1: Deploying the Frontend on Netlify (Free)

Netlify will host your web dashboard globally for free. We have already included a `netlify.toml` file at the root of your project to automate this!

### Instructions:
1. Push your latest code to your **GitHub Repository**.
2. Log in to [Netlify.com](https://www.netlify.com/) (Sign up free with GitHub).
3. Click **"Add new site"** → **"Import an existing project"** → Select **GitHub**.
4. Choose your `jartvis` repository.
5. Netlify will automatically read `netlify.toml`:
   * **Publish directory:** `jarvis_hub/public`
   * **Build command:** *(Leave empty or default)*
6. Click **"Deploy Site"**.
7. *Done!* You will get a live public link (e.g., `https://jarvis-ai-hub.netlify.app`).

---

## 🌩️ Step 2: Deploying the Backend on Oracle Cloud OCI (Forever Free Tier)

Oracle Cloud gives you an **"Always Free"** Linux Server (up to 4 CPU Cores & 24 GB RAM) which is powerful enough to run Python, Node.js, and Headless Chrome 24/7!

### Instructions to Claim Your Server:
1. Go to [Oracle Cloud Free Tier](https://www.oracle.com/cloud/free/) and click **"Start for free"**.
2. Complete account registration (Oracle requires a credit/debit card for identity verification, but will NOT charge you for Always Free ARM Ampere instances).
3. Once logged into the Oracle Cloud Dashboard:
   * Go to **Compute** → **Instances** → **Create Instance**.
   * **Name:** `jarvis-brain-24-7`
   * **Image:** Select **Ubuntu 24.04 LTS** (or Ubuntu 22.04).
   * **Shape:** Select **Ampere (ARM) - VM.Standard.A1.Flex** → Set to **4 Cores** and **24 GB RAM** (Always Free eligible!).
   * **SSH Keys:** Click **"Generate a key pair for me"** and download your private key (`.key` file).
4. Click **Create** and wait 1 minute for your server IP address!

---

## 🔗 Step 3: Launching JARVIS on Oracle Cloud

Once your server is running, connect to it from your laptop terminal and start JARVIS:

```bash
# 1. SSH into your Oracle Cloud Linux server
ssh -i /path/to/your-ssh-key.key ubuntu@<YOUR_ORACLE_PUBLIC_IP>

# 2. Install Git, Python3, Node.js, and Chromium
sudo apt update && sudo apt install -y git python3-venv python3-pip nodejs npm chromium-browser

# 3. Clone your JARVIS repository
git clone https://github.com/<your-username>/jartvis.git
cd jartvis

# 4. Install dependencies
python3 -m venv jarvis-env
source jarvis-env/bin/activate
pip install -r requirements.txt
cd jarvis_hub && npm install && cd ..

# 5. Start JARVIS 24/7 in the background using Screen or SystemD
screen -S jarvis
./start_jarvis_hub.sh
```
*(Press `CTRL+A` then `D` to detach from screen—JARVIS will keep running 24/7 forever even when you disconnect or turn off your laptop!)*
