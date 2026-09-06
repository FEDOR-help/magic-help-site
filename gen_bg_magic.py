# -*- coding: utf-8 -*-
"""Генерация фонового изображения для сайта «Магическая помощь» через HF FLUX."""
import io
import os
from huggingface_hub import InferenceClient

MODEL = "black-forest-labs/FLUX.1-schnell"

PROMPT = (
    "Mystical pale background image: an ancient sage in a long hooded dark robe stands "
    "beside a still forest lake at night, holding a crooked wooden staff in his left hand, "
    "his right hand laid gently on the head of a large white wolf sitting at his side. "
    "Dense dark forest all around, full moon reflected in the calm lake water, soft silver "
    "moonlight, light mist over the water. Very pale, muted, low-contrast watercolor, subtle "
    "and faded so it works as a webpage background, no text, no watermark, nothing sharp "
    "in the center, atmospheric, ethereal, widescreen composition."
)

NEG = "text, watermark, logo, bright saturated colors, high contrast, sharp details, people in center"

OUT = r"D:\13\images\bg_magic.jpg"


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    token = None
    with open(r"D:\.env", encoding="utf-8", errors="replace") as f:
        for line in f:
            if line.startswith("HUGGINGFACE_TOKEN="):
                token = line.split("=", 1)[1].strip()
    if not token:
        print("NO_TOKEN")
        return
    client = InferenceClient(token=token)
    print("Генерирую через", MODEL)
    img = client.text_to_image(
        PROMPT,
        model=MODEL,
        negative_prompt=NEG,
        guidance_scale=3.5,
        num_inference_steps=4,
        width=1536,
        height=1024,
    )
    img.save(OUT, "JPEG", quality=90)
    kb = os.path.getsize(OUT) // 1024
    print("OK", OUT, kb, "KB")


if __name__ == "__main__":
    main()