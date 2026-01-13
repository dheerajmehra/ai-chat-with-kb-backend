# Troubleshooting Guide

## Common Issues

### ModuleNotFoundError when runnia ng uvicorn

**Error:**
```
ModuleNotFoundError: No module named 'aiofiles'
```

**Solution:**
1. Make sure your virtual environment is activated:
   ```bash
   source venv/bin/activate
   ```
   You should see `(venv)` in your terminal prompt.

2. Verify dependencies are installed:
   ```bash
   pip list | grep aiofiles
   ```

3. If not installed, install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run uvicorn from within the activated venv:
   ```bash
   uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
   ```

**Alternative:** Use the helper script:
```bash
./run_server.sh
```

### Wrong Python interpreter

If you're still getting errors, check which Python is being used:

```bash
which python
which uvicorn
```

Both should point to `venv/bin/` directory. If not, activate the venv:
```bash
source venv/bin/activate
```

### PDF Library Errors

**Error:** `PDF_LIBRARY setting not found` or library import fails

**Solution:**
1. Check your `.env` file exists and has:
   ```env
   PDF_LIBRARY=pdfplumber
   ```

2. Verify the library is installed:
   ```bash
   pip list | grep -E "pdfplumber|PyMuPDF"
   ```

3. Install if missing:
   ```bash
   pip install pdfplumber
   ```

### Configuration Errors

**Error:** Missing environment variables

**Solution:**
1. Copy the example env file:
   ```bash
   cp env.example .env
   ```

2. Edit `.env` with your settings (at minimum set `PDF_LIBRARY`)

3. For development, you can use:
   ```env
   PDF_LIBRARY=pdfplumber
   VECTOR_STORE_TYPE=local
   EMBEDDING_PROVIDER=sentence-transformers
   ```

### Port Already in Use

**Error:** `Address already in use`

**Solution:**
1. Find what's using port 8000:
   ```bash
   lsof -i :8000
   ```

2. Kill the process or use a different port:
   ```bash
   uvicorn api.main:app --reload --host 0.0.0.0 --port 8001
   ```

### Import Errors in Test Scripts

**Error:** `ModuleNotFoundError` when running test scripts

**Solution:**
Always activate the virtual environment first:
```bash
source venv/bin/activate
python test_pipeline.py ...
```

## Quick Health Check

Run this to verify everything is set up correctly:

```bash
source venv/bin/activate
python test_installation.py
```

If all checks pass, your environment is ready!

