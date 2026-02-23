# RTX 3060 12GB + Ryzen 5800XT Build Guide
## From Blank Drive to Full AI Development Environment

**Hardware:** Ryzen 5800XT (AM4) + RTX 3060 12GB + NVMe SSD
**Goal:** Dual-boot Windows 11 (music production/DAW) + Linux (AI dev, Claude Code, local LLMs)

---

## Table of Contents

1. [Linux Distro Selection](#1-linux-distro-selection)
2. [Dual Boot: Windows 11 + Linux](#2-dual-boot-windows-11--linux)
3. [Python Virtual Environment (DO THIS FIRST)](#3-python-virtual-environment-do-this-first)
4. [NVIDIA Drivers + CUDA Toolkit](#4-nvidia-drivers--cuda-toolkit)
5. [Ollama + Local LLMs](#5-ollama--local-llms)
6. [Model Catalog: What Runs on 12GB](#6-model-catalog-what-runs-on-12gb)
7. [Claude Code CLI](#7-claude-code-cli)
8. [Gemini CLI](#8-gemini-cli)
9. [Python + Node.js Dev Environment](#9-python--nodejs-dev-environment)
10. [Multi-AI Agentic Workspace Setup](#10-multi-ai-agentic-workspace-setup)
11. [Simultaneous Models & RAG Configurations](#11-simultaneous-models--rag-configurations)
12. [Quick Reference: Complete Install Script](#12-quick-reference-complete-install-script)

---

## 1. Linux Distro Selection

### Recommendation: Ubuntu 24.04 LTS (minimal install + i3 or Sway)

After researching 6 major distros (Ubuntu, Pop!_OS, CachyOS, Fedora, NixOS, Linux Mint), **Ubuntu 24.04 LTS with a minimal install** is the best fit for this build:

| Factor | Why Ubuntu Wins |
|--------|----------------|
| **NVIDIA/CUDA** | NVIDIA's primary target. Every CUDA release is tested on Ubuntu first |
| **Ollama** | Best-tested platform. Install script works perfectly |
| **Claude Code** | Explicitly supported on Ubuntu 20.04+ |
| **AI/ML community** | Every tutorial, Stack Overflow answer, and blog post assumes Ubuntu |
| **Familiar** | Same `apt` system you used on Lubuntu |
| **Resource efficient** | Minimal install + i3/Sway = 300-500 MB RAM at idle |
| **Dual boot** | GRUB handles it cleanly |

### Distro Comparison (for reference)

| Distro | NVIDIA Ease | CUDA Support | Resource Use | AI Community | Learning Curve |
|--------|-------------|-------------|-------------|-------------|---------------|
| **Ubuntu 24.04 LTS** | Excellent | Best-in-class | Moderate (minimal=low) | Unmatched | Low |
| Pop!_OS 24.04 | Best (pre-installed) | Excellent | High (COSMIC: 1.6-2.4GB) | Very Good | Low |
| CachyOS | Very Good | Good (AUR) | Excellent | Growing | High (Arch-based) |
| Fedora 42 | Poor | Problematic | Good | Good | Medium |
| NixOS | Fair | Good (improving) | Excellent | Niche | Very High |
| Linux Mint 22 XFCE | Good | Fair (manual) | Excellent | Fair | Lowest |

**Why not Pop!_OS?** The NVIDIA ISO with pre-installed drivers is tempting, but the new COSMIC desktop has memory leak issues (1.6-2.4GB idle, climbing over time). You want your RAM for LLMs, not desktop chrome.

**Why not Fedora?** CUDA on Fedora is genuinely painful. NVIDIA only supports specific Fedora versions, GCC version mismatches, drivers break after kernel updates. Dealbreaker for AI work.

**Why not CachyOS?** Best raw performance (~10% throughput gain), but Arch-based maintenance and smaller AI community. Great second distro once you're comfortable.

### Ubuntu Setup: Lightweight Terminal-Focused

Instead of the default GNOME desktop (1.2-1.5GB RAM idle), install one of:

| Option | RAM Idle | Style | Install |
|--------|----------|-------|---------|
| **i3wm** | ~300 MB | Tiling, keyboard-driven | `sudo apt install i3` |
| **Sway** | ~350 MB | Wayland tiling (i3 successor) | `sudo apt install sway` |
| **Ubuntu Server + tmux** | ~150 MB | No GUI at all | Install server edition |

Then add a GPU-accelerated terminal:
```bash
sudo apt install alacritty    # or kitty
```

---

## 2. Dual Boot: Windows 11 + Linux

### 2.1 Pre-Build Checklist

- [ ] Windows 11 USB installer (use Media Creation Tool from microsoft.com)
- [ ] Ubuntu 24.04 LTS USB installer (use Rufus in GPT/UEFI mode, or `dd`)
- [ ] NVMe SSD installed
- [ ] Monitor, keyboard, mouse connected
- [ ] Internet connection (Ethernet preferred for Linux driver install)

### 2.2 BIOS/UEFI Configuration

**On first boot, enter BIOS (usually DEL or F2 on AM4 boards):**

1. Set boot mode to **UEFI** (not Legacy/CSM)
2. Enable **XMP/DOCP** for your RAM (get full speed)
3. Leave **Secure Boot enabled** (Ubuntu supports it)
4. Set boot order: USB first, NVMe second
5. Save and exit

### 2.3 Partition Strategy

**For a 1TB NVMe SSD:**

| Partition | Size | Format | Purpose |
|-----------|------|--------|---------|
| EFI System (ESP) | 512 MB | FAT32 | Shared bootloaders (auto-created by Windows) |
| Microsoft Reserved | 16 MB | — | Auto-created by Windows |
| **Windows (C:)** | **250 GB** | NTFS | Windows 11 + DAW + plugins + samples |
| **Shared Data** | **200 GB** | NTFS | Accessible from both OSes (projects, audio files) |
| **Linux Root (/)** | **150 GB** | ext4 | Linux OS + dev tools + Docker images |
| **Linux Swap** | **16 GB** | swap | Match RAM for hibernate support |
| **Linux Home (/home)** | **Remaining (~350 GB)** | ext4 | User files, Ollama models (~50GB+), code |

**For a 2TB drive:** Double the Windows, Shared, and Home allocations.

**For a 500GB drive:** Cut Shared to 100GB, Home to 100GB. Consider an external drive for Ollama models.

### 2.4 Step-by-Step: Install Windows 11

1. Boot from Windows 11 USB (select UEFI boot device)
2. Choose **Custom: Install Windows only (advanced)**
3. Delete ALL existing partitions on the blank drive
4. Click **New** and create a partition of **250 GB** (256,000 MB)
   - Windows auto-creates EFI (100MB) + MSR (16MB) + Recovery partitions
5. **Leave the remaining space UNALLOCATED** — Linux will use it
6. Select the 250GB partition, click **Next**
7. Complete Windows installation, create your account
8. Run Windows Update until fully current
9. Install your DAW and music production software
10. **Disable BitLocker:** Settings → Privacy & Security → Device Encryption → OFF
    - (Windows 11 24H2 enables this aggressively — check after updates)
11. **Disable Fast Startup:** Control Panel → Power Options → "Choose what the power buttons do" → Uncheck "Turn on fast startup"
    - This prevents NTFS hibernation issues when Linux mounts Windows partitions

### 2.5 Step-by-Step: Install Ubuntu 24.04 LTS

1. Boot from Ubuntu USB (select UEFI boot device)
2. Choose **Install Ubuntu**
3. Select language, keyboard layout
4. Choose **Minimal installation** (no office suite, no games)
5. Check **Install third-party software** (includes NVIDIA drivers)
6. At "Installation type," select **Something else** (manual partitioning)
7. In the unallocated space, create:

   | Click "+" | Size | Type | Mount Point |
   |-----------|------|------|-------------|
   | First | 200 GB (204800 MB) | NTFS | — (shared data, no mount point yet) |
   | Second | 150 GB (153600 MB) | ext4 | `/` |
   | Third | 16 GB (16384 MB) | swap area | — |
   | Fourth | Remaining | ext4 | `/home` |

8. Set **"Device for boot loader installation"** to the EFI System Partition
9. Click **Install Now**
10. Complete timezone, username, password setup
11. Reboot — GRUB should show both **Ubuntu** and **Windows Boot Manager**

### 2.6 Post-Install: Mount Shared Data Partition

```bash
# Find the NTFS partition
sudo blkid | grep ntfs

# Create mount point
sudo mkdir -p /mnt/shared

# Add to /etc/fstab for auto-mount (replace UUID with yours)
echo "UUID=YOUR-NTFS-UUID  /mnt/shared  ntfs3  defaults,uid=1000,gid=1000  0  0" | sudo tee -a /etc/fstab

# Mount now
sudo mount -a
```

### 2.7 Important 2025-2026 Notes

- **ntfs3** kernel driver (not ntfs-3g) is now the default — faster, more reliable NTFS access
- Ubuntu 25.04+ supports encrypted dual boot with LUKS from the GUI installer
- **systemd-boot** is gaining popularity as a GRUB alternative (auto-detects Windows)
- Check BitLocker status after every major Windows update — 24H2 re-enables it silently

---

## 3. Python Virtual Environment (DO THIS FIRST)

> **Why this matters:** On Termux we installed packages globally as root — that's how we ended up fighting pandas 3.0 vs lightrag wanting <2.4, safetensors needing ANDROID_API_LEVEL hacks, and `--no-deps` workarounds. Never again. A virtual environment isolates your AI packages from the system Python so nothing can conflict.

### 3.1 The Rule

**NEVER `pip install` anything globally.** Every project gets its own venv. System Python stays untouched.

```bash
# Install venv support (Ubuntu 24.04)
sudo apt update
sudo apt install -y python3-pip python3-venv python3-dev
```

### 3.2 Create Your Main AI Virtual Environment

```bash
# Create it once
python3 -m venv ~/ai-env

# Activate it (you'll do this every time you open a terminal for AI work)
source ~/ai-env/bin/activate

# Your prompt changes to show you're inside the venv:
# (ai-env) user@machine:~$

# Verify pip points to the venv, not system
which pip
# Should show: /home/youruser/ai-env/bin/pip  (NOT /usr/bin/pip)
which python
# Should show: /home/youruser/ai-env/bin/python
```

### 3.3 Auto-Activate on Login (Optional)

Add to `~/.bashrc` so the venv activates every time you open a terminal:

```bash
echo '# Auto-activate AI virtual environment' >> ~/.bashrc
echo 'source ~/ai-env/bin/activate' >> ~/.bashrc
```

Or if you prefer manual activation, create an alias:

```bash
echo 'alias ai="source ~/ai-env/bin/activate"' >> ~/.bashrc
```

Then just type `ai` to activate.

### 3.4 Per-Project Venvs (For Isolated Work)

For the multi-ai-agentic-workspace specifically:

```bash
cd ~/projects/multi-ai-agentic-workspace/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

This keeps workspace dependencies separate from your general AI environment.

### 3.5 What Goes Where

| Environment | What to Install | Why |
|------------|----------------|-----|
| **System Python** (`sudo apt install python3-xyz`) | ONLY system tools (e.g., `python3-venv` itself) | Managed by Ubuntu's package manager, never breaks |
| **~/ai-env** (main venv) | numpy, torch, model2vec, lightrag-hku, etc. | Your general AI toolkit, pip-managed |
| **project/.venv** (per-project) | Project-specific requirements.txt | Isolated per project, reproducible |

### 3.6 Lesson from Termux

What we dealt with on the phone and why venvs prevent it:

| Termux Problem | Venv Solution |
|---------------|--------------|
| `pip install` as root, global | `pip install` inside venv, user-owned |
| pandas 3.0 (system) vs lightrag wants <2.4 | Venv has its own pandas version, no conflict |
| safetensors build failure → ANDROID_API_LEVEL hack | x86_64 + venv = clean pip install, no hacks |
| `python3` was 3.13, `pip` installed to 3.12 | Venv pins one Python version, `pip` and `python` always match |
| Couldn't uninstall broken packages without breaking others | `rm -rf ~/ai-env && python3 -m venv ~/ai-env` — fresh in 2 seconds |

> **From here forward, every `pip install` command in this guide assumes you have activated a virtual environment.** If your prompt doesn't show `(ai-env)` or `(.venv)`, activate first.

---

## 4. NVIDIA Drivers + CUDA Toolkit

### 3.1 Install NVIDIA Driver

The RTX 3060 (Ampere, compute capability 8.6) is fully supported.

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Method 1: Auto-detect best driver (recommended)
sudo ubuntu-drivers autoinstall

# Method 2: Specific stable version
sudo apt install nvidia-driver-570

# REBOOT REQUIRED
sudo reboot
```

**Verify after reboot:**
```bash
nvidia-smi
```
Expected output: RTX 3060, 12288 MiB VRAM, Driver Version: 570.xx

### 3.2 Install CUDA Toolkit

**Current versions (Feb 2026):**

| CUDA Version | Min Driver | Status |
|-------------|-----------|--------|
| CUDA 12.8 | Driver ≥ 570 | **Recommended** (safe, compatible) |
| CUDA 13.0 | Driver ≥ 580 | Latest (requires newer driver) |
| CUDA 13.1 | Driver ≥ 590 | Newest (bleeding edge) |

**Install CUDA 12.8 (recommended for driver 570):**

```bash
# Add NVIDIA CUDA repository
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2404/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb
sudo apt update

# Install CUDA toolkit
sudo apt install cuda-toolkit-12-8

# Add to PATH (add to ~/.bashrc)
echo 'export PATH=/usr/local/cuda/bin:$PATH' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc

# Verify
nvcc --version
```

### 3.3 Install cuDNN

```bash
# From NVIDIA's apt repository (already added above)
sudo apt install cudnn-cuda-12

# Verify
cat /usr/include/cudnn_version.h | grep CUDNN_MAJOR -A 2
```

### 3.4 Install NVIDIA Container Toolkit (for Docker)

```bash
# Add repository
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | \
  sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

# Install
sudo apt update
sudo apt install nvidia-container-toolkit

# Configure Docker
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

# Test GPU in Docker
docker run --rm --gpus all nvidia/cuda:12.8.0-base-ubuntu24.04 nvidia-smi
```

---

## 5. Ollama + Local LLMs

### 4.1 Install Ollama

```bash
# One-command install (binary + systemd service)
curl -fsSL https://ollama.com/install.sh | sh

# Verify
ollama --version
systemctl status ollama
```

The installer:
- Downloads the Ollama binary
- Creates an `ollama` system user
- Sets up a systemd service (auto-starts on boot)
- Auto-detects your RTX 3060

### 4.2 Configure Ollama for Your GPU

```bash
# Edit the systemd service for optimizations
sudo systemctl edit ollama.service
```

Add:
```ini
[Service]
Environment="OLLAMA_FLASH_ATTENTION=1"
Environment="OLLAMA_HOST=0.0.0.0:11434"
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl restart ollama
```

| Variable | Purpose |
|----------|---------|
| `OLLAMA_FLASH_ATTENTION=1` | Faster token generation on NVIDIA GPUs |
| `OLLAMA_HOST=0.0.0.0:11434` | Listen on all interfaces (for LAN access) |
| `OLLAMA_MODELS=/path/to/dir` | Custom model storage (default: ~/.ollama/models) |
| `OLLAMA_KV_CACHE_TYPE=q8_0` | Compress KV cache — lets 14B models handle longer context |
| `OLLAMA_MAX_LOADED_MODELS=2` | Keep 2 models loaded simultaneously |
| `OLLAMA_KEEP_ALIVE=-1` | Don't auto-unload models after 5 min |

### 4.3 Service Management

```bash
sudo systemctl start ollama       # Start
sudo systemctl stop ollama        # Stop
sudo systemctl restart ollama     # Restart
sudo systemctl status ollama      # Status
journalctl -u ollama -f           # Live logs
```

### 4.4 Pull Your Models

```bash
# ===== TIER 1: Fits comfortably, fast inference =====

ollama pull llama3.1:8b              # 4.9 GB — general purpose, fastest
ollama pull qwen2.5-coder:7b        # 4.7 GB — best coding at this size
ollama pull gemma2:9b               # 5.8 GB — punches above its weight
ollama pull nomic-embed-text        # 274 MB — embeddings for RAG

# ===== TIER 2: Tight fit, higher quality =====

ollama pull deepseek-r1:14b         # 9.0 GB — best reasoning
ollama pull qwen2.5-coder:14b      # 9.0 GB — best coding quality
ollama pull gemma3:12b              # 8.1 GB — multimodal (text+image)
ollama pull mistral-nemo            # 7.5 GB — strong multilingual
ollama pull phi4                    # 9.1 GB — STEM/math/reasoning

# ===== SPECIALTY =====

ollama pull granite3-guardian:8b    # 5.8 GB — safety guardrails
ollama pull granite3-guardian:2b    # 1.6 GB — lightweight safety
ollama pull granite-code:8b         # 4.9 GB — IBM code model

# Total storage needed: ~70-80 GB
```

### 4.5 Quick Test

```bash
# Interactive chat
ollama run llama3.1:8b

# API call
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.1:8b",
  "prompt": "Explain knowledge graphs in 3 sentences"
}'

# Check GPU usage while a model is running
nvidia-smi
```

---

## 6. Model Catalog: What Runs on 12GB

### Complete Reference Table

| Model | `ollama pull` | Quant | VRAM | Fits 12GB? | Speed (tok/s) | Best For |
|-------|--------------|-------|------|-----------|--------------|---------|
| Llama 3.1 8B | `llama3.1:8b` | Q4_K_M | ~5.5 GB | Yes (comfortable) | ~45 | General, fastest |
| Qwen2.5-Coder 7B | `qwen2.5-coder:7b` | Q4_K_M | ~5.5 GB | Yes (comfortable) | 40-50 | Coding |
| Gemma 2 9B | `gemma2:9b` | Q4_K_M | ~6.5 GB | Yes (comfortable) | 30-40 | General purpose |
| Granite Guardian 2B | `granite3-guardian:2b` | Default | ~2.5 GB | Trivially | 80-100+ | Safety (tiny) |
| nomic-embed-text | `nomic-embed-text` | F16 | ~0.3 GB | Trivially | N/A | Embeddings/RAG |
| Mistral Nemo 12B | `mistral-nemo` | Q4_K_M | ~8.5 GB | Yes | 20-30 | General, multilingual |
| Granite Guardian 8B | `granite3-guardian:8b` | Q5_K_M | ~7 GB | Yes | 35-45 | Safety guardrails |
| Granite Code 8B | `granite-code:8b` | Q4_K_M | ~6 GB | Yes | 40-50 | Code (IBM) |
| Gemma 3 12B | `gemma3:12b` | Q4_K_M | ~10 GB | Yes (short ctx) | 15-25 | Multimodal |
| DeepSeek-R1 14B | `deepseek-r1:14b` | Q4_K_M | ~10 GB | Yes (short ctx) | 15-25 | Reasoning, math |
| Qwen2.5-Coder 14B | `qwen2.5-coder:14b` | Q4_K_M | ~10 GB | Yes (short ctx) | 15-22 | Coding (best quality) |
| Phi-4 14B | `phi4` | Q4_K_M | ~10 GB | Yes (short ctx) | 15-22 | STEM, planning |

### Quantization Guide

| Quantization | Quality | Size vs FP16 | When to Use |
|-------------|---------|-------------|-------------|
| Q4_K_M | Very Good | ~25% | **Default choice for 12GB** |
| Q5_K_M | Better | ~31% | When model barely fits |
| Q6_K | Near-lossless | ~38% | Only for ≤9B models on 12GB |
| Q8_0 | Excellent | ~50% | Only for ≤8B models on 12GB |
| FP16 | Original | 100% | Only for tiny models (≤3B) |

**Rule of thumb:** Q4_K_M is the sweet spot for 12GB. It cuts model size by 75% with minimal quality loss.

### Context Length Warning

14B models at Q4_K_M use ~9-10 GB for weights alone. The **KV cache** grows with context length:
- 4K context: +0.5 GB
- 8K context: +1 GB
- 16K context: +2 GB
- 32K context: +4 GB (won't fit alongside a 14B model)

**Tip:** Set `OLLAMA_KV_CACHE_TYPE=q8_0` to halve KV cache size, or `q4_0` to quarter it. Minor quality impact.

---

## 7. Claude Code CLI

### 6.1 Install (Native Installer — No Node.js Required)

```bash
# One-command install
curl -fsSL https://claude.ai/install.sh | bash

# Verify
claude --version
```

This installs the `claude` binary and adds it to PATH. Auto-updates included.

### 6.2 Authentication

**Option A: API Key (recommended for developers)**

```bash
# Get a key from console.anthropic.com
export ANTHROPIC_API_KEY="sk-ant-your-key-here"

# Persist it
echo 'export ANTHROPIC_API_KEY="sk-ant-YOUR-KEY"' >> ~/.bashrc
source ~/.bashrc
```

**Option B: Claude Pro/Max Subscription**

```bash
claude
# Select "Claude Pro/Max subscription" when prompted
# Authenticate via browser
```

**Option C: Enterprise (AWS Bedrock)**

```bash
export CLAUDE_CODE_USE_BEDROCK=1
export AWS_REGION=us-east-1
# Configure AWS credentials
```

### 6.3 First Run

```bash
# Start interactive session
claude

# In a project directory (picks up CLAUDE.md context)
cd ~/projects/multi-ai-agentic-workspace
claude
```

---

## 8. Gemini CLI

### 7.1 Install (Requires Node.js 18+)

```bash
# Install Node.js first (see Section 8)
npm install -g @google/gemini-cli

# Verify
gemini --version
```

### 7.2 Authentication

**Option A: Google Account Login (free tier)**

```bash
gemini
# Select: "Login with Google"
# Follow browser flow
```

Free tier: 60 requests/min, 1,000 requests/day.

**Option B: API Key**

```bash
# Get key from https://aistudio.google.com/apikey
export GEMINI_API_KEY="your-key-here"
echo 'export GEMINI_API_KEY="your-key-here"' >> ~/.bashrc
```

### 7.3 Configuration

```bash
# Create persistent config
mkdir -p ~/.gemini
cat > ~/.gemini/.env << 'EOF'
GEMINI_API_KEY=your-key-here
EOF

# Create user-level context (like CLAUDE.md)
echo "I prefer concise responses with code examples" > ~/.gemini/GEMINI.md
```

---

## 9. Python + Node.js Dev Environment

### 8.1 Python

```bash
# Python 3.12 is included in Ubuntu 24.04
python3 --version

# Install pip and venv
sudo apt install python3-pip python3-venv python3-dev

# Create a virtual environment for AI work
python3 -m venv ~/ai-env
source ~/ai-env/bin/activate

# Install key packages
pip install numpy networkx fastapi uvicorn httpx
pip install google-genai anthropic
pip install model2vec lightrag-hku sqlite-vec
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128
```

### 8.2 Node.js

```bash
# Via NodeSource (LTS)
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs

# Verify
node --version   # v22.x
npm --version

# Or via nvm (multiple versions)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.0/install.sh | bash
source ~/.bashrc
nvm install 22
nvm use 22
```

### 8.3 Essential Dev Tools

```bash
sudo apt install git curl wget build-essential
sudo apt install docker.io docker-compose

# Add yourself to docker group (no sudo for docker commands)
sudo usermod -aG docker $USER
# Log out and back in for this to take effect
```

---

## 10. Multi-AI Agentic Workspace Setup

Once all the above is installed, clone and run the workspace:

```bash
# Clone
cd ~/projects
git clone https://github.com/Eyalio84/Multi-AI.git multi-ai-agentic-workspace
cd multi-ai-agentic-workspace

# Backend
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# sqlite-vec now works on x86_64!
pip install sqlite-vec

# Start backend
uvicorn main:app --host 0.0.0.0 --port 8000 &

# Frontend
cd ../frontend
npm install
npm run dev &

# Verify
curl http://localhost:8000/api/health
# Open http://localhost:5173 in browser
```

### Connect Local LLMs to KG Studio

The KG Studio's RAG Chat and Ingestion tabs can be configured to use Ollama instead of (or alongside) the Gemini API. The embedding service can use nomic-embed-text via Ollama's embedding endpoint:

```bash
# Ollama API is compatible at:
# http://localhost:11434/api/generate  (chat)
# http://localhost:11434/api/embeddings (embeddings)
```

### Upgrades from Termux

| Feature | Termux (Phone) | Desktop (RTX 3060) |
|---------|---------------|-------------------|
| sqlite-vec | Unavailable | **Works** — native vector search |
| model2vec | Installed (CPU) | **GPU-accelerated** |
| lightrag-hku | pandas version conflict | **Full compatibility** |
| Graph analytics | CPU-bound | **Faster** (more RAM, faster CPU) |
| KG visualization | Mobile layout | **Full desktop layout** |
| Local LLMs | None | **12GB of models** |
| RAG Chat | Gemini API only | **Local + API hybrid** |

---

## 11. Simultaneous Models & RAG Configurations

Since nomic-embed-text uses only ~300 MB VRAM, you can always run it alongside a chat model.

### Combinations That Work on 12GB

| Embedding | Chat Model | Combined VRAM | Verdict |
|-----------|-----------|--------------|---------|
| nomic-embed-text (0.3 GB) | Llama 3.1 8B (5.5 GB) | ~6 GB | **Excellent** — 6 GB headroom |
| nomic-embed-text (0.3 GB) | Qwen2.5-Coder 7B (5.5 GB) | ~6 GB | **Excellent** — best for coding RAG |
| nomic-embed-text (0.3 GB) | Gemma 2 9B (6.5 GB) | ~7 GB | **Good** — 5 GB headroom |
| nomic-embed-text (0.3 GB) | Mistral Nemo 12B (8.5 GB) | ~9 GB | **OK** — 3 GB headroom |
| nomic-embed-text (0.3 GB) | Gemma 3 12B (10 GB) | ~10.5 GB | **Tight** — short context only |
| nomic-embed-text (0.3 GB) | DeepSeek-R1 14B (10 GB) | ~10.5 GB | **Tight** — short context only |

### Triple-Model Safety Stack

```bash
# Safety + Chat + Embeddings — fits in 12GB
ollama pull granite3-guardian:2b    # 2.5 GB — safety monitor
ollama pull llama3.1:8b             # 5.5 GB — chat
ollama pull nomic-embed-text        # 0.3 GB — embeddings
# Total: ~8.3 GB — comfortable fit
```

### Recommended Configurations

**Daily Driver (coding):**
```bash
ollama pull qwen2.5-coder:7b       # Primary: coding
ollama pull nomic-embed-text        # RAG embeddings
# VRAM: ~6 GB, plenty of headroom
```

**Maximum Quality (reasoning):**
```bash
ollama pull deepseek-r1:14b         # Primary: deep reasoning
ollama pull nomic-embed-text        # RAG embeddings
# VRAM: ~10.5 GB, tight but works at 4K-8K context
```

**Full RAG Pipeline (KG Studio):**
```bash
ollama pull gemma2:9b               # Chat model for RAG answers
ollama pull nomic-embed-text        # Embedding model for search
# VRAM: ~7 GB, excellent for the multi-ai-agentic-workspace
```

---

## 12. Quick Reference: Complete Install Script

Run this after dual-boot is set up and you're booted into Ubuntu:

```bash
#!/bin/bash
# === RTX 3060 AI Development Environment Setup ===
# Run as your user (not root), it will sudo when needed

set -e

echo "=== Step 1: System Update ==="
sudo apt update && sudo apt upgrade -y

echo "=== Step 2: Essential Tools ==="
sudo apt install -y git curl wget build-essential python3-pip python3-venv python3-dev

echo "=== Step 3: NVIDIA Driver ==="
sudo apt install -y nvidia-driver-570
echo "!!! REBOOT REQUIRED after this step !!!"
echo "Run 'sudo reboot', then re-run this script starting from Step 4"
echo "To skip Steps 1-3 on re-run, comment them out"
read -p "Press Enter to continue (after reboot) or Ctrl+C to reboot now..."

echo "=== Step 4: Verify GPU ==="
nvidia-smi

echo "=== Step 5: CUDA Toolkit 12.8 ==="
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2404/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb
sudo apt update
sudo apt install -y cuda-toolkit-12-8
echo 'export PATH=/usr/local/cuda/bin:$PATH' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc
nvcc --version

echo "=== Step 6: cuDNN ==="
sudo apt install -y cudnn-cuda-12

echo "=== Step 7: Docker + NVIDIA Container Toolkit ==="
sudo apt install -y docker.io
sudo usermod -aG docker $USER
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | \
  sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt update
sudo apt install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

echo "=== Step 8: Node.js 22 LTS ==="
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs

echo "=== Step 9: Ollama ==="
curl -fsSL https://ollama.com/install.sh | sh

echo "=== Step 10: Configure Ollama ==="
sudo mkdir -p /etc/systemd/system/ollama.service.d
sudo tee /etc/systemd/system/ollama.service.d/override.conf << 'EOF'
[Service]
Environment="OLLAMA_FLASH_ATTENTION=1"
Environment="OLLAMA_HOST=0.0.0.0:11434"
EOF
sudo systemctl daemon-reload
sudo systemctl restart ollama

echo "=== Step 11: Pull Models ==="
ollama pull llama3.1:8b
ollama pull qwen2.5-coder:7b
ollama pull nomic-embed-text
ollama pull gemma2:9b
echo "Pull more models manually: deepseek-r1:14b, gemma3:12b, phi4, etc."

echo "=== Step 12: Claude Code ==="
curl -fsSL https://claude.ai/install.sh | bash

echo "=== Step 13: Gemini CLI ==="
npm install -g @google/gemini-cli

echo "=== Step 14: Python Virtual Environment (CRITICAL — never pip install globally) ==="
python3 -m venv ~/ai-env
source ~/ai-env/bin/activate
echo '# Auto-activate AI virtual environment' >> ~/.bashrc
echo 'source ~/ai-env/bin/activate' >> ~/.bashrc

echo "=== Step 15: Python AI Packages (inside venv) ==="
pip install --upgrade pip
pip install numpy networkx fastapi uvicorn httpx
pip install google-genai anthropic
pip install model2vec lightrag-hku sqlite-vec safetensors tokenizers
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128

echo "=== Step 16: Clone Multi-AI Workspace ==="
mkdir -p ~/projects
cd ~/projects
git clone https://github.com/Eyalio84/Multi-AI.git multi-ai-agentic-workspace

echo ""
echo "============================================"
echo "  SETUP COMPLETE!"
echo "============================================"
echo ""
echo "Next steps:"
echo "  1. Set API keys in ~/.bashrc:"
echo "     export ANTHROPIC_API_KEY='sk-ant-...'"
echo "     export GEMINI_API_KEY='...'"
echo "  2. Run 'claude' to authenticate Claude Code"
echo "  3. Run 'gemini' to authenticate Gemini CLI"
echo "  4. Start the workspace:"
echo "     cd ~/projects/multi-ai-agentic-workspace/backend"
echo "     source ~/ai-env/bin/activate"
echo "     uvicorn main:app --host 0.0.0.0 --port 8000"
echo "  5. In another terminal:"
echo "     cd ~/projects/multi-ai-agentic-workspace/frontend"
echo "     npm install && npm run dev"
echo ""
```

---

## Appendix: What Can't Run on 12GB

For reference, these require more VRAM:

| Model | Size | Min VRAM | Why |
|-------|------|----------|-----|
| Llama 3.1 70B | Q4_K_M | ~40 GB | Too large even at Q2 |
| DeepSeek-R1 (full) | 671B MoE | ~160 GB | Enterprise-scale |
| Qwen2.5 72B | Q4_K_M | ~42 GB | Needs A100/H100 |
| Mixtral 8x22B | Q4_K_M | ~80 GB | MoE, needs multi-GPU |

For these, continue using Claude/Gemini APIs — that's the hybrid strategy: **local for volume, API for quality**.

---

*Last updated: 2026-02-23*
*Hardware: Ryzen 5800XT + RTX 3060 12GB*
*Target OS: Ubuntu 24.04 LTS (minimal + i3/Sway)*
