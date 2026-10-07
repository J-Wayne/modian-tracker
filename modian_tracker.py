# -*- coding: utf-8 -*-

import asyncio
import re
from datetime import datetime
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
from playwright.async_api import async_playwright

URL = "https://zhongchou.modian.com/item/160465.html"
INTERVAL = 60
OUT = Path("data")
CSV = OUT / "history.csv"
PNG = OUT / "curve.png"


def get_amount(text):
    nums = []
    for m in re.finditer(r"[¥￥]\s*([\d,]+(?:\.\d+)?)", text):
        try:
            nums.append(float(m.group(1).replace(",", "")))
        except ValueError:
            pass
    return max(nums) if nums else None


def plot():
    df = pd.read_csv(CSV)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp")

    plt.figure(figsize=(10, 5))
    plt.plot(df["timestamp"], df["amount_cny"], marker="o", linewidth=1.8)
    plt.title("Funding Amount Over Time")
    plt.ylabel("CNY")
    plt.grid(alpha=0.25)
    plt.tight_layout()
    plt.savefig(PNG, dpi=150)
    plt.close()


async def main():
    OUT.mkdir(exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(locale="zh-CN")

        while True:
            now = datetime.now()

            try:
                await page.goto(URL, wait_until="domcontentloaded", timeout=60000)
                await page.wait_for_timeout(3000)
                text = await page.locator("body").inner_text()

                amount = get_amount(text)
                if amount is None:
                    print(f"[{now:%H:%M:%S}] 未识别到金额")
                else:
                    if not CSV.exists():
                        CSV.write_text("timestamp,amount_cny\n", encoding="utf-8-sig")
                    with CSV.open("a", encoding="utf-8-sig") as f:
                        f.write(f"{now:%Y-%m-%d %H:%M:%S},{amount:.2f}\n")
                    plot()
                    print(f"[{now:%H:%M:%S}] ¥{amount:,.2f}")
            except Exception as e:
                print(f"[{now:%H:%M:%S}] 失败：{e}")

            await asyncio.sleep(INTERVAL)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("已停止")
