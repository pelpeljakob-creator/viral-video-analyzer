import asyncio
import json
import os
import re

import httpx
from playwright.async_api import async_playwright

from config import settings
from models.schemas import VideoMeta

_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36"


async def download_video(url: str, output_dir: str) -> VideoMeta:
    """Download Douyin video: fetch detail via Playwright → extract URL → download."""
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "video.mp4")

    # Step 1: Get detail JSON
    detail_path = os.path.join(output_dir, "detail.json")
    if os.path.exists(detail_path):
        with open(detail_path, "r", encoding="utf-8") as f:
            detail = json.load(f)
    else:
        detail = await _fetch_detail_playwright(url)
        if detail:
            with open(detail_path, "w", encoding="utf-8") as f:
                json.dump(detail, f, ensure_ascii=False)

    if not detail or "aweme_detail" not in detail:
        raise RuntimeError("无法获取视频详情，请确保链接有效")

    aweme = detail["aweme_detail"]
    meta = _parse_meta(aweme)

    # Step 2: Download video
    video_url = _get_best_video_url(aweme)
    if not video_url:
        raise RuntimeError("未找到视频下载地址")

    await _download_file(video_url, output_path)

    if not os.path.exists(output_path) or os.path.getsize(output_path) < 1000:
        raise RuntimeError("视频下载失败或文件过小")

    return meta


async def _fetch_detail_playwright(url: str) -> dict | None:
    """Use Playwright to open Douyin page and intercept the detail API response."""
    aweme_id = _extract_aweme_id(url)
    if not aweme_id:
        aweme_id = await _resolve_short_url(url)
    if not aweme_id:
        raise RuntimeError(f"无法从链接提取视频ID: {url}")

    # Ensure URL is in full format
    if "douyin.com/video/" not in url:
        url = f"https://www.douyin.com/video/{aweme_id}"

    detail_json = None

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=_UA,
            viewport={"width": 1280, "height": 720},
            locale="zh-CN",
        )
        page = await context.new_page()

        # Intercept the detail API response
        response_future = asyncio.get_event_loop().create_future()

        async def handle_response(response):
            nonlocal detail_json
            if response_future.done():
                return
            resp_url = response.url
            if "aweme/v1/web/aweme/detail" in resp_url and aweme_id in resp_url:
                try:
                    body = await response.json()
                    if body.get("aweme_detail"):
                        detail_json = body
                        if not response_future.done():
                            response_future.set_result(body)
                except Exception:
                    pass

        page.on("response", handle_response)

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            # Wait for the API response (max 20s)
            await asyncio.wait_for(asyncio.shield(response_future), timeout=20)
        except asyncio.TimeoutError:
            # Try to extract from page SSR data as fallback
            detail_json = await _extract_from_ssr(page, aweme_id)
        except Exception:
            pass
        finally:
            await browser.close()

    return detail_json


async def _extract_from_ssr(page, aweme_id: str) -> dict | None:
    """Try to extract video detail from page's SSR RENDER_DATA."""
    try:
        content = await page.evaluate("""() => {
            const el = document.querySelector('script[id="RENDER_DATA"]');
            if (!el) return null;
            return decodeURIComponent(el.textContent);
        }""")
        if not content:
            return None
        data = json.loads(content)
        # Search for video detail in the data tree
        return _find_aweme_detail(data, aweme_id)
    except Exception:
        return None


def _find_aweme_detail(data: dict, aweme_id: str) -> dict | None:
    """Recursively search for aweme_detail in SSR data."""
    if isinstance(data, dict):
        if "aweme_detail" in data or "awemeDetail" in data:
            detail = data.get("aweme_detail") or data.get("awemeDetail")
            if detail and isinstance(detail, dict):
                return {"aweme_detail": detail}
        for v in data.values():
            result = _find_aweme_detail(v, aweme_id)
            if result:
                return result
    elif isinstance(data, list):
        for item in data:
            result = _find_aweme_detail(item, aweme_id)
            if result:
                return result
    return None


def _extract_aweme_id(url: str) -> str | None:
    match = re.search(r"video/(\d+)", url)
    return match.group(1) if match else None


async def _resolve_short_url(url: str) -> str | None:
    """Resolve v.douyin.com short URL to get aweme_id."""
    try:
        async with httpx.AsyncClient(
            follow_redirects=True,
            headers={"User-Agent": _UA},
        ) as client:
            resp = await client.head(url, timeout=10)
            final_url = str(resp.url)
            return _extract_aweme_id(final_url)
    except Exception:
        return None


def _parse_meta(aweme: dict) -> VideoMeta:
    stats = aweme.get("statistics", {})
    video = aweme.get("video", {})
    author = aweme.get("author", {})
    duration = video.get("duration", 0)
    if duration > 1000:
        duration = duration / 1000
    return VideoMeta(
        title=aweme.get("desc", ""),
        author=author.get("nickname", ""),
        author_id=author.get("sec_uid", author.get("uid", "")),
        likes=stats.get("digg_count"),
        comments=stats.get("comment_count"),
        shares=stats.get("share_count"),
        duration=duration,
        thumbnail_url=video.get("cover", {}).get("url_list", [None])[0],
    )


def _get_best_video_url(aweme: dict) -> str | None:
    video = aweme.get("video", {})
    bit_rate = video.get("bit_rate", [])
    if bit_rate:
        sorted_rates = sorted(bit_rate, key=lambda x: x.get("bit_rate", 0), reverse=True)
        for rate in sorted_rates:
            urls = rate.get("play_addr", {}).get("url_list", [])
            for u in urls:
                if "douyinvod.com" in u:
                    return u
            if urls:
                return urls[0]
    play_addr = video.get("play_addr", {})
    urls = play_addr.get("url_list", [])
    for u in urls:
        if "douyinvod.com" in u:
            return u
    return urls[0] if urls else None


async def _download_file(url: str, output_path: str):
    cmd = [
        "curl", "-L", "-o", output_path,
        "-H", f"User-Agent: {_UA}",
        "-H", "Referer: https://www.douyin.com/",
        "--max-time", "120", "--retry", "2", "-s",
        url,
    ]
    process = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await process.communicate()
    if process.returncode != 0:
        raise RuntimeError(f"下载失败: {stderr.decode()[:200]}")
