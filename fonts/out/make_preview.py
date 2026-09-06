# -*- coding: utf-8 -*-
"""Превью шрифта «Фёдор» в PNG."""
import io
from PIL import Image, ImageFont, ImageDraw

FONT = r"D:\13\fonts\out\Fedor-Regular.ttf"
OUT = r"D:\13\fonts\out\preview.png"

samples = [
    "АБВГДЕЁЖЗИЙК",
    "ЛМНОПРСТУФХ",
    "ЦЧШЩЪЫЬЭЮЯ",
    "а б в г д е ж з и й клм",
    "0123456789",
    "!?,:;-\u00ab\u00bb()",
    "МАГИЧЕСКАЯ ПОМОЩЬ",
    "ФЁДОР 2026",
]

size = 72
pad = 40
line_h = size + 26
img_w = 1900
img_h = pad * 2 + line_h * len(samples)

img = Image.new("RGB", (img_w, img_h), "#f7f5f2")
d = ImageDraw.Draw(img)
font = ImageFont.truetype(FONT, size)

y = pad
d.text((pad, y - 10), "Шрифт Фёдор (руническо-готическая кириллица)", fill=(109, 74, 143),
       font=ImageFont.truetype(FONT, 30))
y += 40
for line in samples:
    d.text((pad, y), line, fill=(36, 31, 43), font=font)
    y += line_h

img.save(OUT)
print("saved", OUT, img.size)