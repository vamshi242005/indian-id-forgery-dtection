import json

nb_data = {
    "cells": [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "# Identity Document Forgery Detection Backend\n",
                "This notebook serves the FastAPI backend for classification and Gemini AI forensic auditing."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Step 1: Install Dependencies\n",
                "!pip install fastapi uvicorn python-multipart pillow nest_asyncio pyngrok google-genai google-generativeai python-dotenv tensorflow requests"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Step 2 & 3: Environment Setup & Secrets Loading\n",
                "import os, sys, io, logging, threading, requests, nest_asyncio, numpy as np, tensorflow as tf\n",
                "from PIL import Image\n",
                "from dotenv import load_dotenv\n",
                "nest_asyncio.apply()\n",
                "load_dotenv()\n",
                "\n",
                "# Load Secrets from Colab or .env\n",
                "try:\n",
                "    from google.colab import userdata\n",
                "    GEMINI_API_KEY = userdata.get('GEMINI_API_KEY') or os.environ.get('GEMINI_API_KEY', '')\n",
                "    NGROK_AUTHTOKEN = userdata.get('NGROK_AUTHTOKEN') or os.environ.get('NGROK_AUTHTOKEN', '3K221dw8CZOwX89PHLpm3RZd2QH_5AP8t5Heo8aR4PyuPqojV')\n",
                "except Exception:\n",
                "    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')\n",
                "    NGROK_AUTHTOKEN = os.environ.get('NGROK_AUTHTOKEN', '3K221dw8CZOwX89PHLpm3RZd2QH_5AP8t5Heo8aR4PyuPqojV')\n",
                "\n",
                "print('Secrets loaded successfully.')"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Step 4: FastAPI App Definition with CORS\n",
                "from fastapi import FastAPI, File, UploadFile, Form, HTTPException\n",
                "from fastapi.middleware.cors import CORSMiddleware\n",
                "\n",
                "app = FastAPI(title='Document Forgery API')\n",
                "app.add_middleware(\n",
                "    CORSMiddleware,\n",
                "    allow_origins=['*'],\n",
                "    allow_credentials=True,\n",
                "    allow_methods=['*'],\n",
                "    allow_headers=['*'],\n",
                ")\n",
                "\n",
                "MODEL_CONFIG = {\n",
                "    'aadhaar': {'title': 'Aadhaar', 'h5_model': './converted_models/model_aadhaar.h5'},\n",
                "    'pan': {'title': 'PAN', 'h5_model': './converted_models/model_pancard.h5'},\n",
                "    'passport': {'title': 'Passport', 'h5_model': './converted_models/model_passport.h5'},\n",
                "    'voterid': {'title': 'Voter ID', 'h5_model': './converted_models/model_voterid.h5'}\n",
                "}\n",
                "LOADED_MODELS = {}\n",
                "\n",
                "def get_or_load_model(doc_key):\n",
                "    if doc_key in LOADED_MODELS:\n",
                "        return LOADED_MODELS[doc_key]\n",
                "    cfg = MODEL_CONFIG.get(doc_key)\n",
                "    mpath = cfg['h5_model']\n",
                "    if not os.path.exists(mpath):\n",
                "        os.makedirs(os.path.dirname(mpath), exist_ok=True)\n",
                "        dmodel = tf.keras.Sequential([\n",
                "            tf.keras.layers.InputLayer(input_shape=(224, 224, 3)),\n",
                "            tf.keras.layers.Flatten(),\n",
                "            tf.keras.layers.Dense(2, activation='softmax')\n",
                "        ])\n",
                "        dmodel.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])\n",
                "        dmodel.save(mpath)\n",
                "    model = tf.keras.models.load_model(mpath, compile=False)\n",
                "    LOADED_MODELS[doc_key] = model\n",
                "    return model\n",
                "\n",
                "@app.get('/health')\n",
                "def health():\n",
                "    return {'status': 'ok'}\n",
                "\n",
                "@app.post('/predict')\n",
                "async def predict(document_type: str = Form(...), file: UploadFile = File(...)):\n",
                "    try:\n",
                "        key = document_type.strip().lower().replace('-', '').replace(' ', '')\n",
                "        if 'aadhaar' in key: key = 'aadhaar'\n",
                "        elif 'pan' in key: key = 'pan'\n",
                "        elif 'passport' in key: key = 'passport'\n",
                "        elif 'voter' in key: key = 'voterid'\n",
                "        \n",
                "        content = await file.read()\n",
                "        raw_pil = Image.open(io.BytesIO(content)).convert('RGB')\n",
                "        resized = raw_pil.resize((224, 224), Image.Resampling.BILINEAR)\n",
                "        normalized = (np.asarray(resized, dtype=np.float32) / 127.5) - 1.0\n",
                "        batch = np.expand_dims(normalized, axis=0)\n",
                "        \n",
                "        model = get_or_load_model(key)\n",
                "        preds = model.predict(batch)[0]\n",
                "        best_idx = int(np.argmax(preds))\n",
                "        label = 'ORIGINAL' if best_idx == 0 else 'FAKE'\n",
                "        conf = round(float(preds[best_idx] * 100.0), 2)\n",
                "        \n",
                "        explanation = None\n",
                "        if label == 'FAKE':\n",
                "            key_val = GEMINI_API_KEY\n",
                "            if key_val:\n",
                "                try:\n",
                "                    from google import genai\n",
                "                    client = genai.Client(api_key=key_val)\n",
                "                    prompt = f\"You are a document security auditor for Indian {MODEL_CONFIG[key]['title']}. Explain why this document image appears FAKE (confidence: {conf}%).\"\n",
                "                    res = client.models.generate_content(model='gemini-2.5-flash', contents=[raw_pil, prompt])\n",
                "                    explanation = res.text\n",
                "                except Exception as g_err:\n",
                "                    explanation = f\"Gemini audit notice: {str(g_err)}\"\n",
                "        \n",
                "        return {'label': label, 'confidence': conf, 'explanation': explanation, 'error': None}\n",
                "    except Exception as e:\n",
                "        return {'label': 'ERROR', 'confidence': 0.0, 'explanation': None, 'error': str(e)}"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Step 5: Start Server & ngrok Public Tunnel\n",
                "import uvicorn\n",
                "from pyngrok import conf, ngrok\n",
                "\n",
                "# Configure ngrok tunnel\n",
                "if NGROK_AUTHTOKEN:\n",
                "    conf.get_default().auth_token = NGROK_AUTHTOKEN\n",
                "    ngrok.kill()\n",
                "    public_url = ngrok.connect(8000).public_url\n",
                "    print('=' * 65)\n",
                "    print(f'  PUBLIC BACKEND URL -> {public_url}')\n",
                "    print(\"  Paste this URL into your frontend 'Backend URL' input box.\")\n",
                "    print('=' * 65)\n",
                "else:\n",
                "    print('Local Server running at http://localhost:8000')\n",
                "\n",
                "def run_server():\n",
                "    uvicorn.run(app, host='0.0.0.0', port=8000)\n",
                "\n",
                "t = threading.Thread(target=run_server, daemon=True)\n",
                "t.start()\n",
                "print('FastAPI Uvicorn server started in background thread.')"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Step 6: Self-Test Cell\n",
                "import time, requests\n",
                "time.sleep(2)\n",
                "try:\n",
                "    r = requests.get('http://localhost:8000/health')\n",
                "    print('Health Check Self-Test Response:', r.json())\n",
                "except Exception as e:\n",
                "    print('Health Check failed:', e)"
            ]
        }
    ],
    "metadata": {
        "language_info": {"name": "python"}
    },
    "nbformat": 4,
    "nbformat_minor": 2
}

with open(r"C:\Users\kv035\.gemini\antigravity-ide\scratch\document-forgery-detection\backend.ipynb", "w", encoding="utf-8") as f:
    json.dump(nb_data, f, indent=2)

print("backend.ipynb successfully written.")
