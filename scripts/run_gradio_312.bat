@echo off
setlocal
set PYTHONPATH=C:\dev\TechChallenge3\Techchalleng3

"C:\Users\ramon\AppData\Local\Python\pythoncore-3.12-64\python.exe" -m pip install --upgrade pip setuptools wheel
"C:\Users\ramon\AppData\Local\Python\pythoncore-3.12-64\python.exe" -m pip install --force-reinstall "gradio==4.44.0" "gradio_client==1.3.0" "huggingface_hub<1.0" "chromadb==0.5.23"
"C:\Users\ramon\AppData\Local\Python\pythoncore-3.12-64\python.exe" -c "import gradio, chromadb, huggingface_hub; print('OK', gradio.__version__, chromadb.__version__, huggingface_hub.__version__)"
"C:\Users\ramon\AppData\Local\Python\pythoncore-3.12-64\python.exe" "C:\dev\TechChallenge3\Techchalleng3\src\ui\gradio_app.py"
