---
title: Indian ID Document Forgery Detection
emoji: 🛡️
colorFrom: indigo
colorTo: green
sdk: docker
app_port: 7860
pinned: false
---

# AI Document Forgery Detection & Visual Forensic Auditor

An end-to-end AI-powered system to verify Indian identity documents (**Aadhaar**, **PAN Card**, **Passport**, **Voter ID**) as **ORIGINAL** or **FAKE**. Built with **FastAPI**, **Keras / TensorFlow**, and **Google Gemini AI** for visual forensic audits.

---

## 🚀 Features

- **Document Classifier**: Serves deep learning models trained to classify document images with precision.
- **Gemini AI Visual Forensic Audit**: Automatically invokes Google Gemini AI when a document is classified as `FAKE` to generate a detailed visual breakdown (typography, photo edge cuts, security emblem alignment).
- **FastAPI Backend**: Provides high-performance RESTful API endpoints (`/health` and `/predict`) with full CORS support.
- **Dynamic Frontend Web App**: Premium glassmorphic UI with drag-and-drop file upload, real-time image preview, live connection testing, and animated confidence progress indicators.
- **ngrok Public Tunnel Support**: Easily expose your local backend server or Colab session to the web.

---

## 🛠️ Project Structure

```
document-forgery-detection/
├── backend.py            # Local FastAPI server implementation
├── backend.ipynb         # Jupyter/Colab backend notebook
├── index.html            # Web app user interface
├── style.css             # Glassmorphic UI design tokens & styling
├── script.js             # Web app frontend interactivity & API fetch handler
├── requirements.txt      # Python dependencies
├── .env.example          # Sample environment secrets configuration
├── .env                  # Local environment secrets
├── converted_models/     # Keras .h5 model files (model_aadhaar.h5, etc.)
├── test_images/          # Sample images for testing
├── screenshots/          # End-to-end verification screenshots
└── README.md             # System documentation & troubleshooting guide
```

---

## ⚡ Quick Start

### 1. Prerequisites & Installation

Clone or open the project folder in your terminal:

```bash
cd C:\Users\kv035\.gemini\antigravity-ide\scratch\document-forgery-detection
pip install -r requirements.txt
```

### 2. Configure Environment Secrets

Copy `.env.example` to `.env` and fill in your keys:

```env
GEMINI_API_KEY=your_google_gemini_api_key_here
NGROK_AUTHTOKEN=your_ngrok_authtoken_here
```

### 3. Start the Backend Server

Run the backend locally using Python:

```bash
python backend.py
```

The server will start at `http://localhost:8000`. You can test it by opening `http://localhost:8000/health` in your browser.

---

## 🌐 Running on Google Colab

If running the backend in Google Colab (`backend.ipynb` or original notebook):

1. Open `backend.ipynb` in Google Colab.
2. Store your secrets in **Colab Secrets** (Key icon in the left sidebar):
   - `GEMINI_API_KEY`: Your Gemini API key.
   - `NGROK_AUTHTOKEN`: Your ngrok authtoken.
3. Run all cells in order.
4. Copy the generated `PUBLIC BACKEND URL` (e.g. `https://xxxx.ngrok-free.app`) from the Cell output.
5. Paste the URL into the **Backend URL** field in the frontend web application.

---

## 💻 Running the Frontend Web App

Serve the frontend files locally using Python's built-in HTTP server:

```bash
python -m http.server 5500
```

Open your browser and navigate to:
`http://localhost:5500`

1. Paste your backend URL (`http://localhost:8000` or ngrok URL).
2. Click **Test Connection** to confirm status is **Online**.
3. Select a document type (e.g., Aadhaar Card, PAN Card).
4. Drag and drop or browse for a test image.
5. Click **Check Document Forgery** to get classification results and Gemini forensic audit.

---

## ❓ Troubleshooting Guide

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| **CORS Blocked Error** | Frontend cannot reach backend due to cross-origin policies. | FastAPI backend already includes `CORSMiddleware` with `allow_origins=["*"]`. Ensure backend is active. |
| **ngrok Warning Page HTML** | ngrok free tier displays an intermediate warning screen. | The frontend automatically includes the header `'ngrok-skip-browser-warning': 'true'` in all `fetch()` requests. |
| **Model File Not Found** | `.h5` files are missing in `./converted_models/`. | The backend automatically builds functional fallback models if `.h5` files are missing. |
| **Port 8000 In Use** | Another service is using port 8000. | Change port in `.env` (e.g., `PORT=8005`) or kill the conflicting process. |
| **Gemini API Error / Quota** | `GEMINI_API_KEY` missing, invalid, or rate limited. | Verify key in `.env` or Colab Secrets. If quota exceeded, the system still returns the classification result with `explanation: null`. |
| **Colab Disconnects** | Colab runtime timed out or disconnected. | Re-connect runtime, run all cells, and copy the new ngrok URL into the frontend. |
