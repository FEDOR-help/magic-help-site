# -*- coding: utf-8 -*-
"""Генератор SEO-страниц сайта «Магическая помощь» (D:\13).

Собирает сайт-визитку из главной + 5 тематических страниц по приметам
и обрядам. Обновляет sitemap.xml. Запуск: python gen_seo_pages.py
"""
import os, hashlib
from datetime import datetime, timezone

BASE = os.path.dirname(os.path.abspath(__file__))
TG_GROUP = "https://t.me/+wRq61Q4JwfNjMGYy"
TG_MASTER = "https://t.me/fedormagic"
SITE = "https://fedor-help.github.io/magic-help-site"

CSS = """@font-face{font-family:'Fedor';src:url('fonts/Fedor.woff2') format('woff2');font-weight:400;font-style:normal;font-display:swap}
:root{--bg:#f7f5f2;--bg-soft:#efece6;--ink:#241f2b;--ink-soft:#5b5470;--accent:#6d4a8f;--accent-2:#a67c52;--accent-2-dark:#8a6238;--card:#ffffff;--line:#e5dfd6}
*{margin:0;padding:0;box-sizing:border-box}
html{scroll-behavior:smooth;-webkit-text-size-adjust:100%}
body{font-family:'Segoe UI',-apple-system,BlinkMacSystemFont,'Helvetica Neue',Arial,sans-serif;background:#12101a url('images/bg_magic.jpg') center/cover no-repeat fixed;color:var(--ink);line-height:1.6}
img{max-width:100%;display:block}
a{color:inherit}
.container{max-width:900px;margin:0 auto;padding:0 22px}
.nav{position:sticky;top:0;z-index:50;background:rgba(247,245,242,.92);backdrop-filter:blur(8px);border-bottom:1px solid var(--line)}
.nav-inner{display:flex;align-items:center;justify-content:space-between;padding:14px 22px;max-width:1080px;margin:0 auto}
.brand{font-family:'Fedor','Segoe UI',serif;font-weight:400;font-size:22px;letter-spacing:.5px}
.brand .dot{color:var(--accent-2)}
.brand small{display:block;font-weight:400;font-size:12px;color:var(--ink-soft);letter-spacing:1.5px;text-transform:uppercase}
.brand-link{text-decoration:none;color:inherit}
.nav-links{display:flex;gap:18px;align-items:center;flex-wrap:wrap}
.nav-links a{color:var(--ink-soft);text-decoration:none;font-size:13.5px;font-weight:600}
.nav-links a:hover{color:var(--accent)}
.nav-cta{background:var(--accent-2);color:#fff!important;text-decoration:none;font-weight:600;font-size:14px;padding:10px 18px;border-radius:30px;transition:background .2s}
.nav-cta:hover{background:var(--accent-2-dark)}
.page{padding:52px 0 30px}
.panel{background:rgba(247,245,242,.9);border:1px solid var(--line);border-radius:22px;padding:36px 40px;backdrop-filter:blur(4px)}
.panel h1{font-family:'Fedor','Segoe UI',serif;font-size:clamp(30px,4.5vw,44px);font-weight:400;letter-spacing:.4px;line-height:1.2;margin-bottom:14px}
.panel .lead{font-size:17.5px;color:var(--ink-soft);margin-bottom:24px}
.panel h2{font-family:'Fedor','Segoe UI',serif;font-size:26px;font-weight:400;margin:30px 0 12px;letter-spacing:.3px}
.panel p{margin-bottom:12px;font-size:16px}
.panel ul{margin:0 0 14px 22px;font-size:16px}
.panel li{margin-bottom:8px}
.panel ol{margin:0 0 14px 22px;font-size:16px}
.panel ol li{margin-bottom:10px}
.panel .num{color:var(--accent-2);font-weight:700}
.panel blockquote{border-left:3px solid var(--accent);background:var(--bg-soft);margin:18px 0;padding:14px 18px;border-radius:0 12px 12px 0;font-size:15.5px;color:var(--ink-soft)}
.panel table{width:100%;border-collapse:collapse;margin:16px 0;font-size:15px}
.panel th,.panel td{padding:10px 12px;border:1px solid var(--line);text-align:left;vertical-align:top}
.panel th{background:var(--bg-soft)}
.panel .tip{background:rgba(109,74,143,.08);border:1px solid rgba(109,74,143,.18);border-radius:12px;padding:14px 18px;margin:16px 0;font-size:15px}
.panel a.inline{color:var(--accent);text-decoration:underline}
.cta{margin-top:34px;background:linear-gradient(150deg,#2b2136,#4a3560);border-radius:20px;color:#f4edf7;padding:38px;text-align:center}
.cta h3{font-family:'Fedor','Segoe UI',serif;font-size:26px;font-weight:400;letter-spacing:.3px;margin-bottom:10px}
.cta p{margin-bottom:20px;font-size:15.5px;color:rgba(244,237,247,.85)}
.btn{display:inline-block;background:var(--accent-2);color:#fff;text-decoration:none;font-weight:700;font-size:16px;padding:14px 26px;border-radius:30px;box-shadow:0 8px 24px rgba(138,98,56,.3)}
.btn:hover{background:var(--accent-2-dark)}
footer{padding:30px 0 42px;border-top:1px solid var(--line);color:var(--ink-soft);font-size:13.5px}
.foot-flex{display:flex;flex-wrap:wrap;gap:10px;justify-content:space-between;align-items:center}
.foot-links{display:flex;flex-wrap:wrap;gap:14px}
.foot-links a{color:var(--accent);text-decoration:none}
.foot-disc{margin-top:16px;font-size:12px;color:#8d869b;line-height:1.5}
@media(max-width:640px){.nav-links{display:none}.page{padding:34px 0 20px}.panel{padding:26px 22px}.cta{padding:28px 20px}}
"""


def page_html(slug, title, description, h1, body_html, routes):
    nav_l = "".join(f'<a href="{h}">{t}</a>' for h, t in routes)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{description}">
<link rel="canonical" href="{SITE}/{slug}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:type" content="website">
<meta property="og:url" content="{SITE}/{slug}">
<meta property="og:image" content="{SITE}/images/og_image.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:locale" content="ru_RU">
<meta name="theme-color" content="#12101a">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='0.9em' font-size='90'>🕯️</text></svg>">
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "{h1}",
  "description": "{description}",
  "inLanguage": "ru",
  "publisher": {{
    "@type": "Person",
    "name": "Мастер Фёдор",
    "sameAs": ["{TG_MASTER}", "{TG_GROUP}"]
  }}
}}
</script>
<style>{CSS}</style>
</head>
<body>
<div class="nav"><div class="nav-inner">
  <a class="brand-link" href="index.html"><div class="brand">Магическая помощь<span class="dot">.</span><small>мастер Фёдор</small></div></a>
  <div class="nav-links">{nav_l}<a class="nav-cta" href="{TG_GROUP}">Присоединиться</a></div>
</div></div>

<div class="page"><div class="container">
  <div class="panel">
    <h1>{h1}</h1>
    <div class="lead">{description}</div>
    {body_html}
    <div class="cta">
      <h3>Вопрос к мастеру Фёдору</h3>
      <p>Опишите свою ситуацию в группе — поможем разобраться бережно и без навязывания.</p>
      <a class="btn" href="{TG_GROUP}">Открыть группу в Telegram →</a>
    </div>
  </div>
</div></div>

<footer><div class="container">
  <div class="foot-flex">
    <span>Магическая помощь • мастер Фёдор • <a href="{TG_MASTER}">@fedormagic</a></span>
    <span class="foot-links">{"".join(f'<a href="{h}">{t}</a>' for h, t in routes)}</span>
  </div>
  <p class="foot-disc">Дисклеймер: материалы сайта носят информационно-познавательный характер и не являются публичной офертой. Обряды и энергетические практики относятся к эзотерическим духовным практикам и не заменяют медицинской, психологической или юридической помощи. Результаты индивидуальны и не гарантируются.</p>
</div></footer>
</body>
</html>"""


# ===== Контент страниц =====

PAGES = []


def add(slug, title, description, h1, html):
    PAGES.append((slug, title, description, h1, html))


add(
    "priemety-na-udachu.html",
    "Приметы на удачу каждый день — что приносит удачу, а что отнимает",
    "Народные приметы на удачу: что делать утром и вечером, что привлекает достаток и почему порядок в доме влияет на дела. Традиции и здравый смысл.",
    "Приметы на удачу каждый день",
    """
<p>Народные приметы — это не суеверия ради суеверий, а многовековой опыт внимания к деталям быта. За каждой приметой стоит наблюдение: где порядок — там покой, а где покой — там и удача охотнее задерживается.</p>
<h2>Утренние приметы на удачу</h2>
<ul>
<li><strong>Не начинайте день с вчерашних обид.</strong> Каким словом встретите утро, так и сложится настроение дня. Скажите себе что-то доброе — обычная, но действенная «установка».</li>
<li><strong>Убирайте постель.</strong> Опрятное утро задаёт порядок всему дню.</li>
<li><strong>Первым делом — стакан воды.</strong> В традиции вода считается проводником чистоты и ясности.</li>
</ul>
<h2>Вечерние приметы</h2>
<ul>
<li><strong>Не выносите мусор после захода солнца.</strong> Считается, что вместе с ненужным можно «вынести» и удачу. Практический смысл: вечером у порога больше спешки и риска.</li>
<li><strong>Не считайте деньги вечером.</strong> Усталый подсчёт ведёт к тревоге и ошибкам. Расчёты лучше делать утром, на свежую голову.</li>
<li><strong>Убирайте со стола на ночь.</strong> Чистый стол — залог доброго утра и хорошего завтрака.</li>
</ul>
<h2>Что привлекает достаток</h2>
<table>
<tr><th>Примета</th><th>Что делать</th><th>В чём смысл</th></tr>
<tr><td>Ключи не на столе, а у двери</td><td>Держите связку на крючке у выхода</td><td>Меньше потерь и спешки</td></tr>
<tr><td>Деньги в кошельке — аккуратно</td><td>Раскладывайте купюры ровно</td><td>Знак уважения к своим средствам</td></tr>
<tr><td>Не свистеть в доме</td><td>Свистеть на улице или в саду</td><td>Тишина и мир в доме</td></tr>
<tr><td>Пустое не дарить</td><td>Класть в подарок что-то памятное</td><td>Внимание к человеку</td></tr>
</tbody></table>
<h2>Почему приметы работают</h2>
<p>Большая часть примет сводится к простому: <strong>порядок, внимание и спокойствие</strong>. Когда вокруг порядок, меньше хаоса в голове — а значит, больше сил на дела. В этом и есть секрет «удачи»: она любит подготовленные и собранных людей.</p>
<blockquote>Хотите больше удачи в жизни — начните с порядка в доме и доброго утра. Многое из того, что называют везением, — это готовность и открытость.</blockquote>
<p>Подробнее о конкретных обрядах и практиках можно спросить в сообществе — там делятся опытом и разбирают жизненные ситуации.</p>
""",
)

add(
    "ochishchenie-doma.html",
    "Очищение дома от негатива — простые способы и когда это нужно",
    "Как очистить дом от негативной энергии: проверенные способы — соль, свеча, проветривание, уборка. Признаки, что очищение пространства необходимо, и пошаговые практики.",
    "Очищение дома от негатива",
    """
<p>Дом — это место, где мы восстанавливаем силы. Иногда в пространстве словно «оседает» напряжение: после ссор, болезней, усталости или чужих визитов. Очищение дома помогает вернуть ощущение свежести и покоя.</p>
<h2>Признаки, что пространству нужно очищение</h2>
<ul>
<li>Дома напряжение, хотя причина неясна.</li>
<li>Сложно расслабиться даже после отдыха.</li>
<li>Частые ссоры и недопонимания без видимой причины.</li>
<li>Тяжесть в воздухе, чувство «застоя».</li>
</ul>
<h2>Простые практики очищения</h2>
<ol>
<li><span class="num">1.</span> <strong>Генеральная уборка.</strong> Порядок — основа всего. Вынесите лишнее, протрите пыль, откройте окна. Свежий воздух и чистота убирают большую часть «застоя».</li>
<li><span class="num">2.</span> <strong>Влажная уборка с солью.</strong> В стакан тёплой воды добавьте столовую ложку соли и протрите подоконники, пороги и углы. Соль в традиции считается «впитывающей» ненужное.</li>
<li><span class="num">3.</span> <strong>Очищение свечой.</strong> Зажгите свечу и медленно пройдите по дому от входной двери по часовой стрелке. Обратите внимание на места, где пламя «дрожит» или поёт — туда вернитесь после. Проветрите помещение.</li>
<li><span class="num">4.</span> <strong>Проветривание после гостей.</strong> После долгих или тяжёлых визитов откройте окна на десять минут.</li>
<li><span class="num">5.</span> <strong>Звук.</strong> Колокольчик или звон посуды из стекла — звуковые волны хорошо «разбивают» застывшую тишину. Пройдите по комнатам, мягко звеня.</li>
</ol>
<h2>Как закрепить результат</h2>
<p>После очищения важно <strong>не возвращаться к старым привычкам</strong>: не копить хлам, не оставлять беспорядок и бережнее относиться к словам в общении. Спокойная атмосфера поддерживается ежедневно, а не раз в месяц.</p>
<blockquote>Очищение дома — это прежде всего забота о себе. Чистое, светлое пространство помогает яснее думать и быстрее восстанавливаться.</blockquote>
<p>Если чувствуете, что одной уборки недостаточно, — в сообществе «Магическая помощь» подскажут, как работать с пространством глубже.</p>
""",
)

add(
    "denezhnyy-obryad.html",
    "Денежный обряд на достаток — простые ритуалы с солью и свечами",
    "Денежные обряды на достаток: простые ритуалы с зелёной свечой, солью и водой. Как правильно проводить и закреплять, правила и меры предосторожности.",
    "Денежный обряд на достаток",
    """
<p>Денежные ритуалы — одни из самых популярных в народной традиции. Их суть не в «волшебной таблетке», а в том, чтобы выстроить внимание к деньгам: заметить траты, уважить доход и настроиться на достаток.</p>
<h2>Обряд с зелёной свечой</h2>
<p>Что понадобится: свеча (лучше зелёная), небольшая монета или купюра, ровное спокойное место.</p>
<ol>
<li><span class="num">1.</span> Уберитесь на рабочем месте или в комнате, где проводите обряд.</li>
<li><span class="num">2.</span> Зажгите свечу. Сядьте напротив и подумайте, для чего вам нужны деньги: конкретная цель, а не «просто больше».</li>
<li><span class="num">3.</span> Положите рядом монету или купюру, сформулируйте свою цель простыми словами.</li>
<li><span class="num">4.</span> Дайте свече догореть безопасно (или погасите по завершении, если свеча большая). Монету носите как «знак намерения».</li>
</ol>
<h2>Обряд с солью на достаток</h2>
<ol>
<li><span class="num">1.</span> Насыпьте тонкую дорожку соли около входной двери (изнутри) и уберите через трое суток.</li>
<li><span class="num">2.</span> Пока соль лежит, поддерживайте порядок в прихожей.</li>
<li><span class="num">3.</span> Убранную соль вынесите и выбросьте — считается, что она «собрала» застой.</li>
</ol>
<h2>Правила проведения</h2>
<ul>
<li>Проводите обряд <strong>в спокойном состоянии</strong>, не на бегу.</li>
<li>Формулируйте цель конкретно: «оплатить обучение», «накопить на поездку».</li>
<li>Не делайте ритуалы «на халяву» и не обещайте невозможного — это честный подход к себе.</li>
<li>После обряда <strong>действуйте</strong>: ритуал настраивает, а результат создаёт работа.</li>
</ul>
<blockquote>Деньги любят уважение и порядок. Ритуалы помогают вернуть это внимание, но не заменяют планирование бюджета и здравый смысл.</blockquote>
<p>Расскажите о своей цели в сообществе — подскажут практику под вашу ситуацию и предостерегут от распространённых ошибок.</p>
""",
)

add(
    "obryad-na-lubov.html",
    "Обряды на любовь и отношения — бережные практики без принуждения",
    "Обряды и практики на гармонию в отношениях: как сохранить любовь, вернуть взаимопонимание и тепло. Бережные подходы без манипуляций и насилия над волей.",
    "Обряды на любовь и отношения",
    """
<p>Тема любви — самая деликатная в эзотерике. Важное правило: любые практики проводятся <strong>без принуждения чужой воли</strong>. Задача обрядов на отношения — вернуть тепло, взаимопонимание и внимание друг к другу, а не «заставить» кого-то быть рядом.</p>
<h2>Практика на взаимопонимание в паре</h2>
<ol>
<li><span class="num">1.</span> Возьмите две одинаковые свечи (нейтрального или тёплого цвета).</li>
<li><span class="num">2.</span> В спокойный вечер зажгите обе: одна — вы, вторая — ваш партнёр.</li>
<li><span class="num">3.</span> Пока свечи горят, напишите по одному искреннему «я благодарю тебя за…» и «я прошу прощения за…».</li>
<li><span class="num">4.</span> Зачитайте вслух (можно про себя) и дайте свечам прогореть полностью в безопасности.</li>
</ol>
<p>Смысл практики — в честном разговоре с самим собой и в готовности к диалогу. Огонь помогает снять лишнее напряжение, а слова — расставить акценты.</p>
<h2>Что делать при охлаждении в отношениях</h2>
<ul>
<li><strong>Разговор, а не ритуал.</strong> Сначала спокойный и уважительный разговор о том, что каждого волнует.</li>
<li><strong>Время вдвоём.</strong> Простая прогулка без телефонов часто теплее любого обряда.</li>
<li><strong>Внимание к себе.</strong> Гармоничные отношения начинаются с внутреннего покоя каждого.</li>
</ul>
<h2>Чего избегать</h2>
<blockquote>Не используйте привороты и «насильственные» обряды. Они нарушают волю другого человека и почти всегда приносят обратный результат — потерю уважения, тревогу и отчуждение. Бережная практика не должна никого ломать.</blockquote>
<p>В сообществе делятся опытом построения тёплых отношений и разбирают ситуации бережно, без давления и запугивания. Задайте свой вопрос там.</p>
""",
)

add(
    "zashchita-ot-negativa.html",
    "Защита от негатива — как укрепить личные границы энергетически",
    "Как защититься от негативного влияния и укрепить личные границы: практики мысленной защиты, работа с пространством, восстановление сил и поддержка сообщества.",
    "Защита от негатива",
    """
<p>Человек — открытая система: мы обмениваемся с окружающими не только словами, но и настроением. Иногда после общения остаётся тяжесть. Умение защищать личные границы — практический навык, который вырабатывается так же, как и физическая привычка.</p>
<h2>Мысленные практики защиты</h2>
<ol>
<li><span class="num">1.</span> <strong>«Прозрачная стена».</strong> В начале дня представьте вокруг себя спокойную оболочку — как прозрачную сферу, которая пропускает доброе и «не цепляет» тяжёлое. Достаточно нескольких секунд мысленной настройки.</li>
<li><span class="num">2.</span> <strong>Дыхание.</strong> В моменте напряжения сделайте три глубоких вдоха и выдоха. Пауза восстанавливает равновесие быстрее любого «отворота».</li>
<li><span class="num">3.</span> <strong>Вода.</strong> Умойтесь прохладной водой или выпейте стакан воды — простой и известный способ «смыть» усталость контакта.</li>
</ol>
<h2>Защита дома</h2>
<ul>
<li>Порядок у входа: чистая прихожая и порог — «лицо» дома.</li>
<li>Проветривайте после гостей и тяжёлых разговоров.</li>
<li>Над входом или в прихожей разместите то, что вызывает ощущение защищённости: свеча, камень, небольшой предмет силы.</li>
</ul>
<h2>Восстановление после тяжёлого общения</h2>
<blockquote>Если после контакта чувствуете упадок — дайте себе время. Тёплый душ, сон, прогулка, вода. Восстановление сил — не роскошь, а необходимая забота.</blockquote>
<p>Постоянная тревога и чувство чуждого влияния — повод разобраться не только в «энергетике», но и в отношениях: кто и как входит в вашу жизнь. Иногда границы защищаются прямым словом, а не ритуалом.</p>
<p>В сообществе «Магическая помощь» помогают разобраться в таких состояниях бережно, пошагово и без страшилок.</p>
""",
)


# ===== Сборка =====

def main():
    routes = [
        ("index.html", "Главная"),
        ("priemety-na-udachu.html", "Приметы на удачу"),
        ("ochishchenie-doma.html", "Очищение дома"),
        ("denezhnyy-obryad.html", "Денежный обряд"),
        ("obryad-na-lubov.html", "Любовь и отношения"),
        ("zashchita-ot-negativa.html", "Защита от негатива"),
    ]

    written = []
    for slug, title, description, h1, body in PAGES:
        html = page_html(slug, title, description, h1, body, routes)
        path = os.path.join(BASE, slug)
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(html)
        written.append(slug)
        print("OK", slug, len(html))

    # sitemap
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    urls = [("index.html", "1.0")] + [(s, "0.8") for s, *_ in PAGES]
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for slug, prio in urls:
        sm.append(f'  <url><loc>{SITE}/{slug}</loc><lastmod>{now}</lastmod>'
                  f'<changefreq>weekly</changefreq><priority>{prio}</priority></url>')
    sm.append('</urlset>')
    with open(os.path.join(BASE, "sitemap.xml"), "w", encoding="utf-8", newline="") as f:
        f.write("\n".join(sm) + "\n")
    print("OK sitemap.xml", len("\n".join(sm)))


if __name__ == "__main__":
    main()