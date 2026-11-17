import gradio as gr

from llm import generate_response

def greet(name):
    return f"Привет, {name}!"


with gr.Blocks(title="Интерфейс для API") as demo:
    dish_input = gr.Textbox(
        label="Что готовим",
        placeholder="Опишите блюдо...",
        lines=3,
    )

    servings = gr.Dropdown(
        choices=["1", "2", "4", "6"],
        value="1",
        label="На сколько человек",
    )

    output_format = gr.Dropdown(
        choices=["Список продуктов", "Список + шаги"],
        value="Список продуктов",
        label="Формат ответа",
    )

    submit_btn = gr.Button("Сгенерировать список покупок")
    answer = gr.Textbox(label="Ответ", lines=10)

    submit_btn.click(
        fn=generate_response,
        inputs=[dish_input, servings, output_format],
        outputs=answer,
    )

if __name__ == "__main__":
    demo.launch()
