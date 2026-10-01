document.addEventListener("DOMContentLoaded", () => {
    // DOM Elements
    const connectionErrorBanner = document.getElementById("connectionErrorBanner");

    const documentTypeSelect = document.getElementById("documentType");
    const dropZone = document.getElementById("dropZone");
    const fileInput = document.getElementById("fileInput");
    const uploadPrompt = document.getElementById("uploadPrompt");
    const imagePreviewContainer = document.getElementById("imagePreviewContainer");
    const imagePreview = document.getElementById("imagePreview");
    const removeImageBtn = document.getElementById("removeImageBtn");

    const checkDocBtn = document.getElementById("checkDocBtn");
    const btnSpinner = document.getElementById("btnSpinner");
    const btnText = checkDocBtn.querySelector(".btn-text");

    const emptyState = document.getElementById("emptyState");
    const errorAlert = document.getElementById("errorAlert");
    const errorTitle = document.getElementById("errorTitle");
    const errorMessage = document.getElementById("errorMessage");

    const resultContainer = document.getElementById("resultContainer");
    const resultBadge = document.getElementById("resultBadge");
    const badgeIcon = document.getElementById("badgeIcon");
    const badgeLabel = document.getElementById("badgeLabel");
    const metaDocType = document.getElementById("metaDocType");
    const confidencePct = document.getElementById("confidencePct");
    const confidenceBar = document.getElementById("confidenceBar");

    const geminiSection = document.getElementById("geminiSection");
    const geminiExplanation = document.getElementById("geminiExplanation");

    let selectedFile = null;

    // Configuration: Auto-configure the backend address
    // In production when served by the FastAPI backend, this remains empty to use relative paths.
    // When using a bundler like Vite/React, this could be: const API_BASE_URL = process.env.API_URL || "";
    let API_BASE_URL = "";
    
    // Auto-detect local development (frontend running separately on port 5500)
    if (window.location.hostname === "localhost" && window.location.port === "5500") {
        API_BASE_URL = "http://localhost:8005";
    }

    // Background Health Check
    async function performSilentHealthCheck() {
        try {
            const resp = await fetch(`${API_BASE_URL}/health`, {
                method: "GET",
                headers: {
                    "ngrok-skip-browser-warning": "true"
                }
            });
            if (!resp.ok) {
                throw new Error("Server not responding with OK status");
            }
        } catch (err) {
            console.warn("Backend health check failed:", err);
            connectionErrorBanner.classList.remove("hidden");
        }
    }

    // Run health check silently on load without blocking UI
    performSilentHealthCheck();

    // Drag and Drop Handling
    ["dragenter", "dragover"].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.add("drag-over");
        });
    });

    ["dragleave", "drop"].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.remove("drag-over");
        });
    });

    dropZone.addEventListener("drop", (e) => {
        const files = e.dataTransfer.files;
        if (files && files.length > 0) {
            handleFileSelect(files[0]);
        }
    });

    fileInput.addEventListener("change", (e) => {
        if (fileInput.files && fileInput.files.length > 0) {
            handleFileSelect(fileInput.files[0]);
        }
    });

    function handleFileSelect(file) {
        if (!file.type.startsWith("image/")) {
            showError("Invalid File Type", "Please upload a valid image file (JPG, PNG, WEBP).");
            return;
        }
        selectedFile = file;
        const reader = new FileReader();
        reader.onload = (e) => {
            imagePreview.src = e.target.result;
            uploadPrompt.classList.add("hidden");
            imagePreviewContainer.classList.remove("hidden");
            checkDocBtn.disabled = false;
            hideError();
        };
        reader.readAsDataURL(file);
    }

    removeImageBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        clearFileSelection();
    });

    function clearFileSelection() {
        selectedFile = null;
        fileInput.value = "";
        imagePreview.src = "";
        imagePreviewContainer.classList.add("hidden");
        uploadPrompt.classList.remove("hidden");
        checkDocBtn.disabled = true;
        hideResults();
    }

    // Submit Action for Forgery Check
    checkDocBtn.addEventListener("click", async () => {
        if (!selectedFile) return;

        hideError();
        hideResults();
        setLoading(true);

        const docType = documentTypeSelect.value;

        const formData = new FormData();
        formData.append("document_type", docType);
        formData.append("file", selectedFile);

        try {
            const response = await fetch(`${API_BASE_URL}/predict`, {
                method: "POST",
                headers: {
                    "ngrok-skip-browser-warning": "true"
                },
                body: formData
            });

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}));
                throw new Error(errData.detail || `Server returned HTTP ${response.status}`);
            }

            const data = await response.json();

            if (data.error) {
                showError("Prediction Error", data.error);
            } else {
                displayResults(data, docType);
            }
        } catch (err) {
            console.error("Verification Request Error:", err);
            showError(
                "Backend Connection Failed",
                `Unable to reach the backend server. Ensure the service is running and CORS is enabled.`
            );
        } finally {
            setLoading(false);
        }
    });

    function displayResults(data, docTypeKey) {
        const docNames = {
            aadhaar: "Aadhaar Card",
            pan: "PAN Card",
            passport: "Passport",
            voterid: "Voter ID"
        };
        metaDocType.textContent = docNames[docTypeKey] || docTypeKey;

        const label = data.label || "UNKNOWN";
        const conf = data.confidence ? data.confidence.toFixed(1) : "0.0";
        confidencePct.textContent = `${conf}%`;
        confidenceBar.style.width = `${Math.min(100, Math.max(0, data.confidence || 0))}%`;

        if (label === "ORIGINAL") {
            resultBadge.className = "result-badge badge-original";
            badgeIcon.className = "fa-solid fa-circle-check";
            badgeLabel.textContent = "ORIGINAL";
            confidenceBar.style.background = "linear-gradient(90deg, #6366f1, #10b981)";
            geminiSection.classList.add("hidden");
        } else {
            resultBadge.className = "result-badge badge-fake";
            badgeIcon.className = "fa-solid fa-triangle-exclamation";
            badgeLabel.textContent = "FAKE DOCUMENT";
            confidenceBar.style.background = "linear-gradient(90deg, #f59e0b, #ef4444)";

            if (data.explanation) {
                geminiExplanation.textContent = data.explanation;
                geminiSection.classList.remove("hidden");
            } else {
                geminiExplanation.textContent = "No Gemini forensic report generated (GEMINI_API_KEY missing or analysis skipped).";
                geminiSection.classList.remove("hidden");
            }
        }

        emptyState.classList.add("hidden");
        resultContainer.classList.remove("hidden");
    }

    function setLoading(isLoading) {
        if (isLoading) {
            checkDocBtn.disabled = true;
            btnSpinner.classList.remove("hidden");
            btnText.textContent = "Analyzing Document...";
        } else {
            checkDocBtn.disabled = !selectedFile;
            btnSpinner.classList.add("hidden");
            btnText.innerHTML = '<i class="fa-solid fa-magnifying-glass"></i> Check Document Forgery';
        }
    }

    function showError(title, msg) {
        errorTitle.textContent = title;
        errorMessage.textContent = msg;
        emptyState.classList.add("hidden");
        resultContainer.classList.add("hidden");
        errorAlert.classList.remove("hidden");
    }

    function hideError() {
        errorAlert.classList.add("hidden");
    }

    function hideResults() {
        resultContainer.classList.add("hidden");
        emptyState.classList.remove("hidden");
    }
});
