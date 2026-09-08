import importlib.metadata as m

for name in ['gradio', 'gradio_client', 'jinja2', 'starlette', 'fastapi', 'anyio', 'pydantic']:
    try:
        print(f'{name}={m.version(name)}')
    except Exception as e:
        print(f'{name}=MISSING:{e}')
