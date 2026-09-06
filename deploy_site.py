#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Создание репозитория magic-help-site (из D:\13) и деплой на GitHub Pages."""
import os, json, base64, subprocess
from datetime import datetime

GIT = r"D:\ContentFactory\portable\git_full\bin\git.exe"
if not os.path.exists(GIT):
    GIT = "git"
SITE_DIR = r"D:\13"
REPO = "FEDOR-help/magic-help-site"
TOR_PROXY = "socks5://127.0.0.1:9050"


def get_token():
    with open(r"D:\.env", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if line.startswith("GITHUB_TOKEN="):
                return line.split("=", 1)[1].strip()
    return ""


def api(url, token, method="GET", data=None):
    import urllib.request
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Authorization", "token " + token)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "magic-deploy")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode() or "{}")


def git(*args, timeout=90):
    cmd = [GIT, "-C", SITE_DIR, "-c", f"https.proxy={TOR_PROXY}"]
    cmd += list(args)
    r = subprocess.run(cmd, capture_output=True, timeout=timeout)
    out = (r.stdout.decode("utf-8", errors="replace") + "\n" + r.stderr.decode("utf-8", errors="replace")).strip()
    return r.returncode, out


def main():
    token = get_token()
    if not token:
        print("НЕТ ТОКЕНА"); return
    print("Токен: OK")

    # 1. Создать репо, если нет
    st, res = api("https://api.github.com/repos/" + REPO, token)
    if st == 404:
        print("Создаю репозиторий...")
        st, res = api("https://api.github.com/user/repos", token, "POST", {
            "name": "magic-help-site",
            "description": "Магическая помощь — сайт-визитка (обряды, ритуалы, энергетические практики)",
            "homepage": "https://FEDOR-help.github.io/magic-help-site/",
            "public": True,
            "has_wiki": False,
            "has_issues": False,
        })
        if st not in (201, 200):
            print("Ошибка создания:", st, res); return
        print("Репозиторий создан")
    elif st == 200:
        print("Репозиторий уже существует")
    else:
        print("Ошибка проверки:", st, res); return

    # 2. Добавить только файлы из D:\13
    git("add", "-A")
    code, out = git("commit", "-m", f"Лендинг «Магическая помощь» {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    if code != 0 and "nothing to commit" not in out.lower():
        print("Коммит:", out[-300:])
    else:
        print("Коммит: OK")

    # 3. remote + push через Tor c extraheader (без токена в URL)
    git("remote", "remove", "origin")
    git("remote", "add", "origin", "https://github.com/" + REPO + ".git")
    header = "Authorization: Basic " + base64.b64encode(("x-access-token:" + token).encode()).decode()
    cmd = [GIT, "-C", SITE_DIR, "-c", f"https.proxy={TOR_PROXY}",
           "-c", f"http.extraheader={header}",
           "push", "-u", "origin", "main"]
    r = subprocess.run(cmd, capture_output=True, timeout=180)
    out = (r.stdout.decode("utf-8", errors="replace") + "\n" + r.stderr.decode("utf-8", errors="replace")).strip()
    if r.returncode == 0:
        print("PUSH: OK")
    else:
        print("PUSH ОШИБКА:", out[-500:])

    # 4. Проверить, что в ветке ТОЛЬКО index.html
    st, tree = api("https://api.github.com/repos/" + REPO + "/git/trees/main?recursive=1", token)
    if st == 200:
        paths = [t.get("path") for t in tree.get("tree", [])]
        print("Файлов в ветке:", len(paths), paths)

    # 5. Включить Pages
    st, res = api("https://api.github.com/repos/" + REPO + "/pages", token, "POST", {
        "source": {"branch": "main", "path": "/"}
    })
    if st in (201, 200):
        print("PAGES: включено")
    else:
        st2, res2 = api("https://api.github.com/repos/" + REPO + "/pages", token)
        if st2 == 200:
            print("PAGES: уже активен", res2.get("html_url"))
        else:
            print("PAGES:", st, res)


if __name__ == "__main__":
    main()