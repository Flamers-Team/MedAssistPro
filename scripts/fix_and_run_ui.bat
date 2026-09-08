@echo off
setlocal
set PYTHONPATH=C:\dev\TechChallenge3\Techchalleng3

"C:\Users\ramon\AppData\Local\Python\pythoncore-3.12-64\python.exe" -m pip install --force-reinstall "gradio==4.44.1" "gradio_client==1.3.0" "jinja2==3.1.6" "markupsafe==2.1.5" "fastapi==0.115.14" "starlette==0.37.2" "chromadb==0.5.23" "huggingface_hub<1.0"

"C:\Users\ramon\AppData\Local\Python\pythoncore-3.12-64\python.exe" -c "import gradio, gradio_client, jinja2, fastapi, starlette; print('OK', gradio.__version__, gradio_client.__version__, jinja2.__version__, fastapi.__version__, starlette.__version__)"

"C:\Users\ramon\AppData\Local\Python\pythoncore-3.12-64\python.exe" -u "C:\dev\TechChallenge3\Techchalleng3\src\ui\gradio_app.py"
