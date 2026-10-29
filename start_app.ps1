Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Agentic AI Data Preprocessing & Quality Analyst Launcher " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Check Local Ollama Status
try {
    $ollamaCheck = Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -Method Get -TimeoutSec 3
    Write-Host "[OK] Local Ollama runtime detected at http://127.0.0.1:11434" -ForegroundColor Green
} catch {
    Write-Host "[INFO] Ollama is not responding on port 11434. Deterministic Python fallback mode will remain active." -ForegroundColor Yellow
}

# 2. Start FastAPI Backend in a new PowerShell window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$PSScriptRoot\backend'; Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force; .\.venv\Scripts\Activate.ps1; python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"
Write-Host "[OK] Started FastAPI Backend on http://127.0.0.1:8000" -ForegroundColor Green

# 3. Start React + Vite Frontend in a new PowerShell window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$PSScriptRoot\frontend'; npm run dev"
Write-Host "[OK] Started React + Vite Frontend on http://127.0.0.1:5173" -ForegroundColor Green