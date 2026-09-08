# -*- coding: utf-8 -*-
"""Деплой user-site fedor-help.github.io из D:\13\_usersite."""
import os, json, base64, subprocess

GIT = r"D:\ContentFactory\portable\git_full\bin\git.exe"
if not os.path.exists(GIT):
    GIT = "git"
SITE_DIR = r"D:\13\_usersite"
REPO = "FEDOR-help/fedor-help.github.io"
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
    git("add", "-A")
    code, out = git("commit", "-m", "user-site redirect + verification files")
    if code != 0 and "nothing to commit" not in out.lower():
        print("Коммит:", out[-200:])
    else:
        print("Коммит: OK")
    git("remote", "remove", "origin")
    git("remote", "add", "origin", "https://github.com/" + REPO + ".git")
    header = "Authorization: Basic " + base64.b64encode(("x-access-token:" + token).encode()).decode()
    cmd = [GIT, "-C", SITE_DIR, "-c", f"https.proxy={TOR_PROXY}",
           "-c", f"http.extraheader={header}",
           "push", "-u", "origin", "main"]
    r = subprocess.run(cmd, capture_output=True, timeout=180)
    out = (r.stdout.decode("utf-8", errors="replace") + "\n" + r.stderr.decode("utf-8", errors="replace")).strip()
    print("PUSH:", "OK" if r.returncode == 0 else "ОШИБКА " + out[-400:])

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