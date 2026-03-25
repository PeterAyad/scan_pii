#!/usr/bin/env python3
import os
import sys
import torch
import subprocess
import warnings
from gliner import GLiNER
from tqdm import tqdm
from tabulate import tabulate

# 1. Silence deprecation and HF warnings
warnings.filterwarnings("ignore", category=UserWarning)
os.environ["TOKENIZERS_PARALLELISM"] = "false"

def is_git_repo(path):
    return subprocess.run(['git', '-C', path, 'rev-parse', '--is-inside-work-tree'], 
                          capture_output=True, text=True).returncode == 0

def get_git_history_blobs(path):
    """Gets all unique file versions (blobs) from history, handling spaces in filenames."""
    try:
        cmd = "git rev-list --all | xargs -L1 git ls-tree -r --full-name"
        output = subprocess.check_output(cmd, shell=True, text=True, cwd=path, stderr=subprocess.DEVNULL)
        
        unique_blobs = {} 
        for line in output.strip().split('\n'):
            if line:
                # Splitting into 4 parts max ensures the file path keeps its spaces
                parts = line.split(None, 3) 
                if len(parts) >= 4:
                    obj_hash = parts[2]
                    file_path = parts[3]
                    unique_blobs[obj_hash] = file_path
        return unique_blobs
    except Exception:
        return {}

def scan_text(model, text, labels, threshold=0.45):
    """Chunks text to avoid 384-token truncation and returns unique findings."""
    findings = set()
    chunk_size = 1000 # Approx 250 tokens, safe for the 384 model limit
    
    for i in range(0, len(text), chunk_size):
        chunk = text[i : i + chunk_size]
        if not chunk.strip(): continue
        
        entities = model.predict_entities(chunk, labels, threshold=threshold)
        for ent in entities:
            findings.add((ent['label'], ent['text'], f"{ent['score']:.2f}"))
    return findings

def main():
    target_dir = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    # Extensions to ignore to save time and VRAM
    ignored_exts = {'.png', '.jpg', '.jpeg', '.gif', '.pdf', '.exe', '.pyc', '.so', '.dll', '.bin', '.zip', '.tar.gz', '.svg', '.woff', '.woff2'}
    labels = ["person", "email", "phone number", "home address", "password", "api key", "secret token", "credit card number"]
    
    all_results = [] # Storage for (File, Type, Value, Confidence, Location)

    print(f"--- 🛡️ scan_pii (Device: {device.upper()}) ---")
    
    # 2. Load model (Try local first to skip internet check/warnings)
    try:
        model = GLiNER.from_pretrained("nvidia/gliner-pii", local_files_only=True).to(device)
    except Exception:
        print("Initial run: Downloading model (~1.8GB)...")
        model = GLiNER.from_pretrained("nvidia/gliner-pii").to(device)

    # --- PHASE 1: Local Files ---
    files_to_scan = []
    for root, dirs, files in os.walk(target_dir):
        if ".git" in root or "__pycache__" in root: continue
        for file in files:
            if not any(file.lower().endswith(ext) for ext in ignored_exts):
                files_to_scan.append(os.path.join(root, file))

    if files_to_scan:
        for file_path in tqdm(files_to_scan, desc="Scanning Workspace", unit="file", leave=False):
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                found = scan_text(model, content, labels)
                for label, text, conf in found:
                    all_results.append([os.path.relpath(file_path, target_dir), label, text, conf, "Live"])
            except Exception: continue

    # --- PHASE 2: Git History ---
    if is_git_repo(target_dir):
        history_items = get_git_history_blobs(target_dir)
        if history_items:
            for obj_hash, file_path in tqdm(history_items.items(), desc="Scanning Git History", unit="blob", leave=False):
                if any(file_path.lower().endswith(ext) for ext in ignored_exts): continue
                try:
                    content = subprocess.check_output(["git", "-C", target_dir, "show", obj_hash], 
                                                   text=True, errors='ignore', stderr=subprocess.DEVNULL)
                    found = scan_text(model, content, labels)
                    for label, text, conf in found:
                        # Append the blob hash for identification
                        all_results.append([f"{file_path} ({obj_hash[:7]})", label, text, conf, "History"])
                except Exception: continue

    # --- FINAL REPORT ---
    print("\n" + "="*80)
    if all_results:
        print(f"🚨 SCAN COMPLETE: {len(all_results)} potential leaks found!\n")
        print(tabulate(all_results, headers=["File/Source", "Type", "Extracted Value", "Conf", "Location"], tablefmt="grid"))
    else:
        print("✅ SCAN COMPLETE: No PII detected. You are safe to push!")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
