import gradio as gr
import base64
import os
import shutil
import json
import unicodedata
import requests

from analyzer import (
    analyze_profile_image,
    analyze_multiple_photos,
    analyze_conversation_image,
    suggest_first_messages_from_profile,
    print_photo_analysis_results  # добавь импорт
)

UPLOAD_DIR = "/tmp/user_uploads"
API_URL = "http://localhost:8000"

def clean_text(text):
    if isinstance(text, str):
        text = text.encode('utf-8', 'replace').decode('utf-8', 'ignore')
        text = ''.join(ch for ch in text if not unicodedata.category(ch).startswith('Cs'))
    return text


def save_uploaded_files_locally(user_name, section, files):
    if not files:
        return []

    # Обернём строку в список, если один файл
    if isinstance(files, str):
        files = [files]

    folder = os.path.join(UPLOAD_DIR, section, user_name)
    if os.path.exists(folder):
        shutil.rmtree(folder)
    os.makedirs(folder, exist_ok=True)

    saved_paths = []
    for i, f in enumerate(files):
        ext = os.path.splitext(f)[1]
        target_path = os.path.join(folder, f"{section}{i}{ext}")
        shutil.copy(f, target_path)
        saved_paths.append(target_path)
    return saved_paths


def run_my_analysis(description_files):
    if not description_files:
        return "❌ Загрузите фото анкеты.", "", gr.update(visible=False), gr.update(visible=False)
    
    file = description_files[0]
    with open(file.name, "rb") as f:
        files = {"file": (file.name, f)}
        resp = requests.post(f"{API_URL}/analyze_profile_image", files=files)

    if resp.ok:
        data = resp.json()
        return clean_text(data["text"]), "Описание выглядит нормально", gr.update(visible=True), gr.update(visible=True)
    else:
        return "❌ Ошибка анализа.", "", gr.update(visible=False), gr.update(visible=False)

def run_partner_analysis(photo_files):
    if not photo_files:
        return "❌ Загрузите фото профиля.", gr.update(visible=False)
    
    files = [("files", (f.name, open(f.name, "rb"))) for f in photo_files]
    resp = requests.post(f"{API_URL}/analyze_multiple_photos", files=files)

    if resp.ok:
        results = resp.json()
        output = ""
        for item in results:
            output += f"📸 **Фото:** {os.path.basename(item['image_path'])}\n"
            output += f"📌 **Рекомендованная позиция:** {item['recommended_position']}\n"
            output += f"🧠 **Класс:** {item['photo_class']} \n"
            output += f"💬 **Фидбек:**\n{item['feedback']}\n---\n"
        return output, gr.update(visible=True)
    else:
        return "❌ Ошибка анализа.", gr.update(visible=False)

def run_dialog_analysis(dialog_files):
    if not dialog_files:
        return "❌ Загрузите скриншот переписки.", gr.update(visible=False)

    file = dialog_files[0]
    with open(file.name, "rb") as f:
        files = {"file": (file.name, f)}
        resp = requests.post(f"{API_URL}/analyze_conversation_image", files=files)

    if resp.ok:
        return clean_text(resp.json()["analysis"]), gr.update(visible=True)
    else:
        return "❌ Ошибка анализа.", gr.update(visible=False)

def run_compat_analysis(photo_files):
    if not photo_files:
        return "❌ Загрузите фото партнёра.", gr.update(visible=False)

    file = photo_files[0]
    with open(file.name, "rb") as f:
        files = {"file": (file.name, f)}
        resp = requests.post(f"{API_URL}/suggest_first_messages", files=files)

    if resp.ok:
        return clean_text(resp.json()["messages"]), gr.update(visible=True)
    else:
        return "❌ Ошибка анализа.", gr.update(visible=False)


with gr.Blocks(css="""
    body {
        background-color: #fff5f8;
        font-family: 'Nunito', sans-serif;
    }
    .gr-button:not(.save-btn) {
        width: 100%;
        background-color: #ffe4ec;
        color: #333;
        border-radius: 12px;
        font-size: 16px;
        padding: 14px;
        margin-bottom: 10px;
        font-weight: bold;
        border: none;
    }
    .gr-button:not(.save-btn):hover {
        background-color: #ffc2d1;
    }
    .card {
        background-color: #ffffff;
        padding: 16px;
        border-radius: 14px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        margin-bottom: 14px;
    }
    .placeholder {
        background: #ffeef3;
        border-radius: 14px;
        padding: 16px;
        color: #555;
        font-size: 15px;
        margin-bottom: 14px;
    }
    .section-title {
        font-size: 18px;
        font-weight: 700;
        color: #6a1b9a;
        margin-bottom: 10px;
    }
    .vibe {
        display: inline-block;
        background: #ffe0f0;
        color: #6a1b9a;
        border-radius: 20px;
        padding: 6px 12px;
        font-size: 14px;
        margin: 4px 4px 0 0;
    }
    .gr-button.save-btn {
        background-color: #ff5c5c !important;
        color: white !important;
        border-radius: 8px;
        height: 42px;
        min-width: 42px;
        font-size: 18px;
        font-weight: bold;
        padding: 0 12px;
        margin-left: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .gr-button.save-btn:hover {
        background-color: #e34b4b !important;
    }
    .gr-file {
        min-height: 50px !important;
    }
""") as app:

    gr.HTML("""
    <div style="text-align: center;">
        <h1 style="color:#6a1b9a;">💘 AI FFG DAITING</h1>
        <p style="color:#666;">ИИ-ментор, который поможет тебе выделиться, понять собеседника и улучшить диалог</p>
    </div>
    """)

    # === Анализ описания профиля
    gr.Markdown("## 💁‍♂️ Анализ описания профиля")
    my_description = gr.File(label="Описание анкеты (изображение)", file_types=["image"], file_count="multiple")
    my_analyze_btn = gr.Button("🔍 Получить советы от ИИ")
    my_advice_photo = gr.Markdown(visible=False)
    my_advice_desc = gr.Markdown(visible=False)
    my_analyze_btn.click(
        fn=run_my_analysis,
        inputs=[my_description],
        outputs=[my_advice_photo, my_advice_desc, my_advice_photo, my_advice_desc]
    )

    gr.Markdown("## 👤 Анализ фотографий профиля")
    partner_photos = gr.File(label="Фото профиля", file_types=["image"], file_count="multiple")
    partner_analyze_btn = gr.Button("🔍 Анализ фото")
    partner_advice_md = gr.Markdown(visible=False)
    partner_analyze_btn.click(
        fn=run_partner_analysis,
        inputs=[partner_photos],
        outputs=[partner_advice_md, partner_advice_md]
    )

    gr.Markdown("## 💬 Анализ диалога")
    dialog_files = gr.File(label="Скрины переписки", file_types=["image", "text"], file_count="multiple")
    dialog_analyze_btn = gr.Button("🔍 Анализировать переписку")
    dialog_advice = gr.Markdown(visible=False)
    dialog_analyze_btn.click(
        fn=run_dialog_analysis,
        inputs=[dialog_files],
        outputs=[dialog_advice, dialog_advice]
    )

    gr.Markdown("## 💞 Как начать диалог")
    compat_file = gr.File(label="Фото собеседника", file_types=["image"], file_count="single")
    compat_analyze_btn = gr.Button("🔍 Предложить фразы для старта")
    compat_result = gr.Markdown(visible=False)
    compat_analyze_btn.click(
        fn=run_compat_analysis,
        inputs=[compat_file],
        outputs=[compat_result, compat_result]
    )

    gr.HTML("<div class='placeholder'>🚀 Загрузите данные выше и начните анализ!</div>")
    gr.HTML("""
    <div class='card'><div class='section-title'>🧠 Подкаты дня</div>
    <ul><li>Ты словно баг, но я бы не стал тебя фиксить.</li><li>Если ты Wi-Fi, то я на 5 ГГц влюблён.</li><li>Ты как промпт — идеальна и эффективна.</li></ul></div>
    """)
    gr.HTML("""
    <div class='card'><div class='section-title'>🤖 Что ИИ умеет</div>
    <div><span class='vibe'>🔥 сексуальность</span><span class='vibe'>😂 юмор</span><span class='vibe'>📚 интеллект</span></div></div>
    """)

app.launch(server_name="0.0.0.0", server_port=7860, share=True)