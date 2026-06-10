# Genesis Setup on Windows

## Recommended Versions
- Python: 3.11
- Node.js: 20+
- GPU drivers: current stable vendor driver

## 1) Create Python Environment
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

## 2) Install PyTorch (Windows)
Use the command from [PyTorch Start Locally](https://pytorch.org/get-started/locally/) for your GPU/CPU setup.

Example (CPU):
```powershell
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

## 3) Install Backend Dependencies
```powershell
pip install -r apps/api/requirements.txt
```

## 4) Verify Genesis Install
```powershell
python apps/api/app/scripts/verify_genesis_install.py
```

Expected output includes `installed=True`.

## 5) Start Backend
```powershell
# Prefer no --reload for Genesis runs (Taichi/LLVM is sensitive to process reload).
uvicorn main:app --app-dir apps/api --host 127.0.0.1 --port 8000
```

For API-only development with auto-reload:
```powershell
uvicorn main:app --reload --app-dir apps/api
```

## Common Windows Troubleshooting
- If `installed=False`, ensure the active shell has `.venv` activated.
- If `torch` import fails, reinstall using the correct wheel command for your hardware.
- If backend starts but `/genesis/status` reports error, open the error text and resolve the missing package/driver.

## UI Behavior When Genesis Is Missing
- Frontend shows `SetupErrorPanel`.
- Simulation run actions are blocked.
- API `/genesis/status` returns `installed=false` and setup instructions.
