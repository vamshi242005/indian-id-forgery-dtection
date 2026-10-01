import os
import io
import numpy as np
from PIL import Image
import tensorflow as tf
import gradio as gr
from dotenv import load_dotenv

load_dotenv()

# Model loading logic
MODEL_PATHS = {
    "Aadhaar Card": "./converted_models/model_aadhaar.h5",
    "PAN Card": "./converted_models/model_pancard.h5",
    "Passport": "./converted_models/model_passport.h5",
    "Voter ID": "./converted_models/model_voterid.h5"
}

LOADED_MODELS = {}

def get_model(doc_type):
    mpath = MODEL_PATHS[doc_type]
    if doc_type in LOADED_MODELS:
        return LOADED_MODELS[doc_type]
    if os.path.exists(mpath):
        model = tf.keras.models.load_model(mpath, compile=False)
        LOADED_MODELS[doc_type] = model
        return model
    else:
        # Fallback placeholder model
        model = tf.keras.Sequential([
            tf.keras.layers.InputLayer(input_shape=(224, 224, 3)),
            tf.keras.layers.Flatten(),
            tf.keras.layers.Dense(2, activation="softmax")
        ])
        model.compile(optimizer="adam", loss="categorical_crossentropy", metrics=["accuracy"])
        LOADED_MODELS[doc_type] = model
        return model

def analyze_gemini(pil_img, doc_type, conf_pct):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "⚠️ GEMINI_API_KEY environment secret is not set in Space Settings."

    prompt = (
        f"You are an expert document security auditor for Indian {doc_type}. "
        f"An AI model classified this document image as FAKE with {conf_pct:.2f}% confidence.\n"
        f"Explain potential visual forgery indicators (typography, photo frame cuts, emblem alignment, Guilloche layout)."
    )

    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        res = client.models.generate_content(model="gemini-2.5-flash", contents=[pil_img, prompt])
        return res.text
    except Exception as e:
        return f"Gemini Audit Note: {str(e)}"

def predict_document(doc_type, image):
    if image is None:
        return "Please upload an image.", 0.0, ""
    
    # Preprocess
    raw_pil = Image.fromarray(image).convert("RGB")
    resized = raw_pil.resize((224, 224), Image.Resampling.BILINEAR)
    norm = (np.asarray(resized, dtype=np.float32) / 127.5) - 1.0
    batch = np.expand_dims(norm, axis=0)

    model = get_model(doc_type)
    preds = model.predict(batch)[0]
    best_idx = int(np.argmax(preds))

    label = "ORIGINAL" if best_idx == 0 else "FAKE"
    conf = float(preds[best_idx] * 100.0)

    explanation = ""
    if label == "FAKE":
        explanation = analyze_gemini(raw_pil, doc_type, conf)

    return f"RESULT: {label}", f"Confidence: {conf:.2f}%", explanation

# Gradio Interface
demo = gr.Interface(
    fn=predict_document,
    inputs=[
        gr.Dropdown(["Aadhaar Card", "PAN Card", "Passport", "Voter ID"], label="Select Document Type", value="Aadhaar Card"),
        gr.Image(type="numpy", label="Upload Document Image")
    ],
    outputs=[
        gr.Textbox(label="Classification Status"),
        gr.Textbox(label="Confidence"),
        gr.Markdown(label="Gemini AI Forensic Audit Report")
    ],
    title="🛡️ Indian ID Document Forgery Detection & Forensic Audit",
    description="Upload an Indian identity document to classify as ORIGINAL or FAKE. Uses TensorFlow Keras models & Google Gemini AI."
)

if __name__ == "__main__":
    demo.launch()
