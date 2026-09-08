import os
import sys
from pathlib import Path

print('sys.executable=', sys.executable)
import gradio
print('gradio=', gradio.__file__)
import jinja2
print('jinja2=', jinja2.__file__)
from starlette.templating import Jinja2Templates

templates_dir = Path(gradio.__file__).resolve().parent / 'templates'
print('templates_dir=', templates_dir)

t = Jinja2Templates(directory=str(templates_dir))
print('template env type=', type(t.env))
try:
    out = t.get_template('frontend/index.html')
    print('template loaded OK', type(out))
except Exception as e:
    import traceback
    traceback.print_exc()
