#!/usr/bin/env python3
"""
این اسکریپت توسط ربات گیت‌هاب (GitHub Actions) هر ۱ ساعت یکبار اجرا می‌شه.
کارش اینه که پوشه‌ی Pack رو بررسی کنه، برای هر زیرپوشه (هر پک) دنبال
زیرپوشه‌های Java و Bedrock بگرده، و آدرس فایل زیپ داخلشون رو پیدا کنه.
نتیجه‌ی نهایی توی فایل packs-data.json کنار index.html ذخیره می‌شه.
سایت (index.html) فقط همین فایل رو می‌خونه و هیچ درخواستی به API گیت‌هاب نمی‌زنه.
"""

import json
import os
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timezone

REPO = os.environ["GITHUB_REPOSITORY"]  # به‌صورت خودکار توسط Actions پر می‌شه: owner/repo
TOKEN = os.environ["GITHUB_TOKEN"]
API_BASE = f"https://api.github.com/repos/{REPO}/contents"


def api_get(path):
    """گرفتن محتوای یک مسیر از مخزن گیت‌هاب. اگه پیدا نشد None برمی‌گردونه."""
    url = f"{API_BASE}/{path}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "pack-bot",
    })
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise


def find_zip(items):
    """پیدا کردن اولین فایل zip داخل یک لیست از آیتم‌های گیت‌هاب."""
    if not isinstance(items, list):
        return None
    for item in items:
        if item.get("type") == "file" and item.get("name", "").lower().endswith(".zip"):
            return item.get("download_url")
    return None


def main():
    root = api_get("Pack")
    packs = []

    if isinstance(root, list):
        dirs = [
            item for item in root
            if item.get("type") == "dir" and not item.get("name", "").startswith(".")
        ]
        for d in dirs:
            name = d["name"]
            encoded = urllib.parse.quote(name)

            java_items = api_get(f"Pack/{encoded}/Java")
            bedrock_items = api_get(f"Pack/{encoded}/Bedrock")

            packs.append({
                "name": name,
                "java": find_zip(java_items),
                "bedrock": find_zip(bedrock_items),
            })

    data = {
        "updatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "packs": packs,
    }

    with open("packs-data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"انجام شد. {len(packs)} پک پیدا شد.")


if __name__ == "__main__":
    main()
