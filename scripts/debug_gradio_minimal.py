import gradio as gr

with gr.Blocks() as demo:
    gr.Textbox(label='Test')

print('STARTING MINIMAL GRADIO APP')
demo.launch(server_name='127.0.0.1', server_port=7861, share=False, prevent_thread_lock=True)
