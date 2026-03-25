# 🛡️ scan_pii

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A high-performance, local-first PII (Personally Identifiable Information) scanner powered by **NVIDIA GLiNER**. It leverages GPU acceleration (CUDA) to scan your current workspace and your **entire Git history** for accidental leaks before they reach the cloud.

### ⚠️ Important Notes
* **First Run:** The script will download the `nvidia/gliner-pii` model (**~1.8GB**). Internet is required for this initial setup **only**; all subsequent scans are 100% offline.
* **Environment:** This setup assumes a `pyenv` virtual environment named **`pytorch-env`**.
* **Pathing:** The global wrapper points to `/home/$(whoami)/.pyenv/versions/pytorch-env/bin/python`.

---

### 📦 Dependencies

Install these within your dedicated `pytorch-env` to enable GPU acceleration and the reporting UI:

| Package | Purpose |
| :--- | :--- |
| **`gliner`** | The core Zero-Shot Named Entity Recognition (NER) model. |
| **`torch`** | Backend for GPU acceleration (CUDA) and model inference. |
| **`tqdm`** | Provides real-time progress bars for large directories and Git history. |
| **`tabulate`** | Formats findings into a clean, readable grid. |

---

### 🚀 Installation

#### 1. Install Dependencies
Activate your environment and install the required libraries:
```bash
pyenv activate pytorch-env
pip install gliner torch tqdm tabulate
```

#### 2. Save the Logic Script
Save the core Python logic (`scan_pii_logic.py`) to your local bin folder:
```bash
mkdir -p ~/.local/bin
# Move your scan_pii_logic.py file into this directory
```

#### 3. Create the Global Wrapper
Create a wrapper in `/usr/local/bin` to allow global access:
```bash
sudo nano /usr/local/bin/scan_pii
```

**Paste the following:**
```bash
#!/bin/bash
# High-performance PII scanner wrapper
/home/$(whoami)/.pyenv/versions/pytorch-env/bin/python ~/.local/bin/scan_pii_logic.py "$@"
```

#### 4. Set Permissions
```bash
sudo chmod +x /usr/local/bin/scan_pii
```

---

### 🛠️ Usage
Navigate to any project or Git repository and run:

```bash
scan_pii .
```

#### Understanding "History" Hits
If the scanner finds PII in your history, it will display the **Git Blob Hash** in parentheses, e.g., `(a52a0c2)`. You can inspect the specific commit by running:
```bash
git show a52a0c2
```

### ✨ Key Features
* **Zero-Shot NLP:** Uses context-aware AI to distinguish sensitive data from code.
* **Smart Chunking:** Automatically slices large files into overlapping windows to prevent model truncation.
* **Deep Git Scan:** Scans every unique version of every file ever committed in your repository's history.
* **CUDA Optimized:** Leverages your GPU for near-instant inference.
* **100% Private:** Your data never leaves your machine. No API calls, no telemetry.

---

### 🧹 Uninstall
```bash
sudo rm /usr/local/bin/scan_pii
rm ~/.local/bin/scan_pii_logic.py
```

---

**Disclaimer:** *This tool is intended to assist in finding PII but does not guarantee 100% detection. Always use `.gitignore` and environment variables for sensitive secrets.*

