from pathlib import Path

try:
    import gradio_client
except Exception as exc:  # pragma: no cover
    raise SystemExit(f"gradio_client not installed: {exc}")

p = Path(gradio_client.__file__).with_name("utils.py")
text = p.read_text(encoding="utf-8")
text = text.replace(
    'if "enum" in schema:',
    'if isinstance(schema, dict) and "enum" in schema:',
)
text = text.replace(
    'if "const" in schema:',
    'if isinstance(schema, dict) and "const" in schema:',
)
p.write_text(text, encoding="utf-8")
print(f"Patched: {p}")
