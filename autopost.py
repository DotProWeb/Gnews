"""
=============================================================================
ঘাটাইল ডট কম (Ghatail.com) - সোশ্যাল মিডিয়া অটো-পোস্টিং ইঞ্জিন (উপায় ১)
ব্লগারে নতুন সংবাদ প্রকাশের সাথে সাথে স্বয়ংক্রিয়ভাবে ফুল-এইচডি ফটোকার্ড তৈরি
করে ফেসবুক পেজে আপলোড এবং কমেন্টে নিউজ লিংক যুক্ত করে।
=============================================================================
"""

import os
import sys
import re
import json
import time
import random
import base64
import html
import shutil
import tempfile
import subprocess
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET

# UTF-8 কনসোল এনকোডিং নিশ্চিতকরণ (Windows/Linux ক্র্যাশ রোধে)
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
if hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# ১. কনফিগারেশন সেটিংস (Configuration)
BLOGGER_FEED_URL = "https://ghataildotcom.blogspot.com/feeds/posts/default?alt=rss"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
CACHE_FILE = os.path.join(SCRIPT_DIR, "posted_cache.json")
TEMPLATE_PATH = os.path.join(SCRIPT_DIR, "photocard_template.html")
DEFAULT_LOGO_PATH = os.path.join(PROJECT_DIR, "logo.png")
if not os.path.exists(DEFAULT_LOGO_PATH):
    DEFAULT_LOGO_PATH = os.path.join(SCRIPT_DIR, "logo.png")

# র্যান্ডম বিজ্ঞাপন ব্যানার পুল (Ad Banner Pool)
AD_BANNER_FILES = [
    "Ghatail Online 20 Mbps Offer Ads.jpg",
    "Ghatail-Online-Ad-Bnner.jpeg",
    "Ghatail Online 20 Mbps Offer Ads.png"
]

AD_BANNER_ONLINE_URLS = [
    "https://raw.githubusercontent.com/DotProWeb/Gnews/main/Ghatail%20Online%2020%20Mbps%20Offer%20Ads.jpg",
    "https://raw.githubusercontent.com/DotProWeb/Gnews/main/Ghatail-Online-Ad-Bnner.jpeg",
    "https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEimaenH2aj-RtLCKo-RubVCjWh_vEedA9vZRclZeKB3Wt5IyTlFOWcNTU3F2D8-0mW-Mkcz8RQSMpP8iyT2pFfHUNINVFB3u0izh22loHe4vy_4rbHpWH_L6klsKyyacb-IM_i1h0SQZ-M2Ke37fvfwPnF-3pm_Ljm8scXUD2u4N1E203L4JJhifkLttpA/s1600/Ghatail-Online-Ad-Bnner.jpeg"
]

def is_same_image(url1, url2):
    """দুটি ইমেজ একই কিনা তা নির্ধারণ করে (Blogger URL ভ্যারিয়েশন হ্যান্ডেল করে)"""
    if not url1 or not url2:
        return False
    u1 = str(url1).strip()
    u2 = str(url2).strip()
    if u1 == u2:
        return True
    u1_clean = re.sub(r'/(s[0-9]+(-c)?|w[0-9]+-h[0-9]+(-c)?)/', '/', u1.split("?")[0].split("#")[0])
    u2_clean = re.sub(r'/(s[0-9]+(-c)?|w[0-9]+-h[0-9]+(-c)?)/', '/', u2.split("?")[0].split("#")[0])
    if u1_clean == u2_clean:
        return True
    b1 = os.path.basename(u1_clean)
    b2 = os.path.basename(u2_clean)
    if b1 and b2 and b1 == b2 and len(b1) > 5:
        return True
    return False

def get_random_ad_banner(exclude_url=None):
    """
    ফটোকার্ডের তলদেশের বিজ্ঞাপনের জন্য র্যান্ডম ব্যানার নির্বাচন করে।
    নিউজ ফিচারড ইমেজ যেন বিজ্ঞাপনে না আসে তা ১০০% নিশ্চিত করে।
    """
    pool = []
    # লোকাল ফাইল থেকে ব্যানার যোগ
    for fname in AD_BANNER_FILES:
        for base_dir in [SCRIPT_DIR, PROJECT_DIR]:
            fpath = os.path.join(base_dir, fname)
            if os.path.exists(fpath) and fpath not in pool:
                pool.append(fpath)

    # অনলাইন সিডিএন ব্যানার ব্যাকআপ
    for url in AD_BANNER_ONLINE_URLS:
        if url not in pool:
            pool.append(url)

    # নিউজ ইমেজের সাথে মিল থাকলে বাদ দেওয়া (যাতে ভুলেও নিউজের ছবি বিজ্ঞাপনে না আসে)
    filtered = []
    for ad in pool:
        if exclude_url and is_same_image(ad, exclude_url):
            continue
        filtered.append(ad)

    if filtered:
        chosen = random.choice(filtered)
        print(f"🎯 [Ad Banner Selector] র্যান্ডম বিজ্ঞাপন ব্যানার নির্বাচিত: {os.path.basename(str(chosen))}")
        return chosen
    return pool[0] if pool else None

# .env ফাইল থেকে লোকাল পরিবেশ ভেরিয়েবল লোড
def _load_env():
    for p in [os.path.join(SCRIPT_DIR, ".env"), os.path.join(PROJECT_DIR, ".env")]:
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            k = k.strip()
                            v = v.strip().strip("'\"")
                            if k not in os.environ or not os.environ[k]:
                                os.environ[k] = v
            except Exception:
                pass

_load_env()

# ফেসবুক পেজ ক্রেডেনশিয়াল (GitHub Secrets বা পরিবেশ ভেরিয়েবল থেকে অগ্রাধিকার পাবে)
FB_PAGE_ID = os.getenv("FB_PAGE_ID", "399463566750054")
FB_PAGE_ACCESS_TOKEN = os.getenv(
    "FB_PAGE_ACCESS_TOKEN",
    "EAAWmZCyxD13YBS3teAB4hC4sR9db3oeFxiHno7dAqJLnhPD9b62JUvVyuKvWZAiPF1aGURkHcuOWo8OLjDWe4oLZBEqQgF3cGm00RhK31TPyCMNKxDKm2IQQ1Tgl2rVH4ZCXJkCD0nfoD24UWDd5sBvZBwY2ktsTMRycq6vJTXlo61gqitlHzHS32121krZBrZATZB7hC8ZB0er3riQIp4rHvyySR"
)

# ৩. টেলিগ্রাম চ্যানেল ক্রেডেনশিয়াল (Optional)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID", "")

# ৪. এক্স/টুইটার API ক্রেডেনশিয়াল (Optional)
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN", "")

# ৫. হোয়াটসঅ্যাপ চ্যানেল ক্রেডেনশিয়াল (Whapi.cloud API)
WHATSAPP_API_URL = os.getenv("WHATSAPP_API_URL", "https://gate.whapi.cloud")
WHATSAPP_API_TOKEN = os.getenv("WHATSAPP_API_TOKEN", "yOkoAL9RE100MEcZHH4Bz3LvYJiTlcgg")
WHATSAPP_CHANNEL_JID = os.getenv("WHATSAPP_CHANNEL_JID", "120363411468889929@newsletter")


def load_cache():
    """পূর্বে পোস্ট করা সংবাদের লিঙ্ক লোড করে"""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_cache(cache):
    """পোস্ট করা সংবাদের লিঙ্ক ক্যাশে সংরক্ষণ করে"""
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving cache: {e}")


def format_bengali_date(pub_date_str):
    """ইংরেজি তারিখ স্ট্রিংকে খাঁটি বাংলা তারিখে রূপান্তর করে (যেমন: ২১ অক্টোবর ২০২৬)"""
    if not pub_date_str:
        return ""
    
    months = {
        'Jan': 'জানুয়ারি', 'Feb': 'ফেব্রুয়ারি', 'Mar': 'মার্চ',
        'Apr': 'এপ্রিল', 'May': 'মে', 'Jun': 'জুন',
        'Jul': 'জুলাই', 'Aug': 'আগস্ট', 'Sep': 'সেপ্টেম্বর',
        'Oct': 'অক্টোবর', 'Nov': 'নভেম্বর', 'Dec': 'ডিসেম্বর'
    }
    en_to_bn = str.maketrans('0123456789', '০১২৩৪৫৬৭৮৯')

    # সাধারণ RSS ফরম্যাট: "Wed, 21 Oct 2026 14:28:34 +0000"
    m = re.search(r'(\d{1,2})\s+([A-Za-z]{3})\s+(\d{4})', pub_date_str)
    if m:
        day, mon, yr = m.groups()
        bn_day = day.translate(en_to_bn)
        bn_mon = months.get(mon, mon)
        bn_yr = yr.translate(en_to_bn)
        return f"{bn_day} {bn_mon} {bn_yr}"

    return pub_date_str


def fetch_latest_posts():
    """ব্লগারের RSS ফিড থেকে সর্বশেষ সংবাদসমূহ ও এইচডি ইমেজ সংগ্রহ করে"""
    req = urllib.request.Request(
        BLOGGER_FEED_URL,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) GhatailBot/2.0"}
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            xml_data = resp.read()
            root = ET.fromstring(xml_data)
            items = []
            for item in root.findall(".//item"):
                title = item.find("title").text if item.find("title") is not None else ""
                link = item.find("link").text if item.find("link") is not None else ""
                pub_date = item.find("pubDate").text if item.find("pubDate") is not None else ""
                desc = item.find("description").text if item.find("description") is not None else ""
                
                # বিজ্ঞাপন বা বিশেষ পোস্ট বাদ দেওয়া
                if "ফটোকার্ড-বিজ্ঞাপন" in title or "photocard-ad" in title:
                    continue

                image_url = ""
                encl = item.find("enclosure")
                if encl is not None and "url" in encl.attrib:
                    image_url = encl.attrib["url"]
                if not image_url and desc:
                    m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', desc)
                    if m:
                        image_url = m.group(1)
                if image_url:
                    # ব্লগারে ফুল-সাইজ এইচডি ইমেজের জন্য /s1600/ রিপ্লেস
                    image_url = re.sub(r'/s[0-9]+(-c)?/', '/s1600/', image_url)

                # স্পন্সর বিজ্ঞাপন ব্যানার ডিটেকশন (পোস্ট বডিতে কাস্টম ব্যানার থাকলে)
                sponsor_img = ""
                m_sp = re.search(r'<img[^>]+(?:class=["\'][^"\']*photocard-sponsor[^"\']*["\']|alt=["\'][^"\']*ফটোকার্ড স্পন্সর[^"\']*["\'])[^>]+src=["\']([^"\']+)["\']', desc)
                if not m_sp:
                    m_sp = re.search(r'<img[^>]+src=["\']([^"\']+)["\'][^>]+(?:class=["\'][^"\']*photocard-sponsor[^"\']*["\']|alt=["\'][^"\']*ফটোকার্ড স্পন্সর[^"\']*["\'])', desc)
                if m_sp:
                    cand_sp = m_sp.group(1).strip()
                    # স্পন্সর ব্যানার যেন মূল সংবাদের ছবির সমান না হয়
                    if cand_sp and not is_same_image(cand_sp, image_url):
                        sponsor_img = cand_sp

                items.append({
                    "title": title.strip(),
                    "link": link.strip(),
                    "date": format_bengali_date(pub_date),
                    "raw_date": pub_date,
                    "image": image_url,
                    "sponsor_image": sponsor_img
                })
            return items
    except Exception as e:
        print(f"❌ RSS ফিড লোড করতে ত্রুটি: {e}")
        return []


def find_headless_browser():
    """সিস্টেমে হেডলেস ক্রোম বা সমমানের ব্রাউজার এক্সিকিউটেবল খুঁজে বের করে"""
    candidates = [
        # Windows
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        # Linux / GitHub Actions runner
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable",
        "/usr/bin/chromium-browser",
        "/usr/bin/chromium",
        shutil.which("google-chrome"),
        shutil.which("chrome"),
        shutil.which("chromium"),
        shutil.which("msedge")
    ]
    for c in candidates:
        if c and os.path.exists(c):
            return c
    return None


def generate_photocard_browser(title, image_url, output_path=None, pub_date="", ad_banner_url=None):
    """
    হেডলেস ক্রোম দিয়ে ১০০% নিখুঁত যুক্তবর্ণযুক্ত ১২০০x৯৬০ এইচডি ব্র্যান্ডেড ফটোকার্ড তৈরি করে
    """
    browser_exe = find_headless_browser()
    if not browser_exe:
        print("⚠️ হেডলেস ব্রাউজার পাওয়া যায়নি। পিলো ফলব্যাকে যাচ্ছি...")
        return None

    if not os.path.exists(TEMPLATE_PATH):
        print(f"⚠️ টেমপ্লেট ফাইল পাওয়া যায়নি: {TEMPLATE_PATH}")
        return None

    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        tpl = f.read()

    # ১. নিউজ ইমেজ বেস৬৪-এ কনভার্ট (অফলাইন দ্রুত রেন্ডারিং ও ব্রাউজার ব্লকিং রোধে)
    img_b64 = image_url or ""
    if image_url and (image_url.startswith("http://") or image_url.startswith("https://")):
        try:
            req = urllib.request.Request(image_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=12) as ir:
                raw = ir.read()
                mime = "image/png" if raw.startswith(b"\x89PNG") else "image/jpeg"
                img_b64 = f"data:{mime};base64," + base64.b64encode(raw).decode()
        except Exception as ie:
            print(f"নিউজ ইমেজ ডাউনলোড সতর্কবার্তা: {ie}")
            img_b64 = image_url

    # ২. লোগো বেস৬৪-এ কনভার্ট
    logo_b64 = ""
    if os.path.exists(DEFAULT_LOGO_PATH):
        try:
            with open(DEFAULT_LOGO_PATH, "rb") as lf:
                logo_b64 = "data:image/png;base64," + base64.b64encode(lf.read()).decode()
        except Exception:
            pass

    # ৩. বিজ্ঞাপন ব্যানার নির্বাচন ও বেস৬৪-এ কনভার্ট (র্যান্ডম ব্যানার পুল থেকে)
    ad_b64 = ""
    if not ad_banner_url or is_same_image(ad_banner_url, image_url):
        ad_source = get_random_ad_banner(exclude_url=image_url)
    else:
        ad_source = ad_banner_url
    if ad_source:
        if os.path.exists(ad_source):
            try:
                with open(ad_source, "rb") as af:
                    mime = "image/png" if ad_source.lower().endswith(".png") else "image/jpeg"
                    ad_b64 = f"data:{mime};base64," + base64.b64encode(af.read()).decode()
            except Exception:
                pass
        elif ad_source.startswith("http://") or ad_source.startswith("https://"):
            try:
                req = urllib.request.Request(ad_source, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=10) as ar:
                    raw = ar.read()
                    mime = "image/png" if raw.startswith(b"\x89PNG") else "image/jpeg"
                    ad_b64 = f"data:{mime};base64," + base64.b64encode(raw).decode()
            except Exception:
                ad_b64 = ad_source

    # ৪. টেমপ্লেট ভেরিয়েবল প্রতিস্থাপন
    rendered = tpl.replace("{{HEADLINE}}", html.escape(title))
    rendered = rendered.replace("{{IMAGE_URL}}", img_b64)
    rendered = rendered.replace("{{LOGO_URL}}", logo_b64)
    rendered = rendered.replace("{{AD_BANNER_URL}}", ad_b64)
    rendered = rendered.replace("{{DATE}}", html.escape(pub_date or "ঘাটাইল ডট কম"))

    # ৪. টেম্পোরারি HTML তৈরি
    temp_html = None
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as tf:
            tf.write(rendered)
            temp_html = tf.name

        if not output_path:
            output_path = os.path.join(SCRIPT_DIR, "last_photocard.png")

        cmd = [
            browser_exe,
            "--headless=new",
            "--disable-gpu",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--hide-scrollbars",
            "--window-size=1080,1080",
            f"--screenshot={os.path.abspath(output_path)}",
            temp_html
        ]

        subprocess.run(cmd, check=True, timeout=30, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
            print(f"✅ [Browser Engine] ১০৮০x১০৮০ ফটোকার্ড সফলভাবে তৈরি হয়েছে: {output_path} ({os.path.getsize(output_path)} bytes)")
            return output_path
    except Exception as e:
        print(f"❌ ব্রাউজার রেন্ডারিং ব্যর্থ: {e}")
    finally:
        if temp_html and os.path.exists(temp_html):
            try:
                os.unlink(temp_html)
            except Exception:
                pass
    return None


def generate_photocard_pillow(title, image_url, output_path=None, pub_date=""):
    """
    Pillow ফলব্যাক ইঞ্জিন (যদি ব্রাউজার অনুপস্থিত থাকে)
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
        width, height = 1080, 1080

        base = None
        if image_url:
            try:
                img_req = urllib.request.Request(image_url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(img_req, timeout=10) as resp:
                    from io import BytesIO
                    base = Image.open(BytesIO(resp.read())).convert("RGB")
            except Exception:
                pass

        if not base:
            base = Image.new("RGB", (width, 580), (15, 23, 42))
        else:
            base = base.resize((width, 580), Image.Resampling.LANCZOS)

        canvas = Image.new("RGB", (width, height), (255, 255, 255))
        canvas.paste(base, (0, 0))
        draw = ImageDraw.Draw(canvas)

        font_candidates = [
            os.path.join(SCRIPT_DIR, "HindSiliguri-Bold.ttf"),
            "C:/Windows/Fonts/HindSiliguri-Bold.ttf",
            "C:/Windows/Fonts/HindSiliguri-SemiBold.ttf",
            os.path.join(SCRIPT_DIR, "kalpurush.ttf"),
            "C:/Windows/Fonts/kalpurush.ttf",
            "C:/Windows/Fonts/Nirmala.ttc",
            "/usr/share/fonts/truetype/kalpurush/kalpurush.ttf",
            "/usr/share/fonts/truetype/noto/NotoSansBengali-Bold.ttf"
        ]
        font_path = next((f for f in font_candidates if f and os.path.exists(f)), None)
        title_font = ImageFont.truetype(font_path, 40) if font_path else ImageFont.load_default()

        # শিরোনাম ড্র
        draw.text((60, 680), title[:70], font=title_font, fill=(185, 28, 28))
        if len(title) > 70:
            draw.text((60, 740), title[70:140], font=title_font, fill=(185, 28, 28))

        # ফুটার বার
        draw.rectangle([(0, height - 70), (width, height)], fill=(15, 23, 42))
        draw.text((40, height - 50), "সাশ্রয়ী মূল্যে নির্ভরযোগ্য ইন্টারনেট ও ডিজিটাল সেবা (০১৭১৩-৩২৮৮০২)", fill=(255, 255, 255))

        if not output_path:
            output_path = os.path.join(SCRIPT_DIR, "last_photocard.png")
        canvas.save(output_path, "PNG")
        print(f"✅ [Pillow Fallback] ১০৮০x১০৮০ ফটোকার্ড তৈরি হয়েছে: {output_path}")
        return output_path
    except Exception as e:
        print(f"❌ পিলো ফলব্যাকেও ত্রুটি: {e}")
        return None


def generate_photocard(title, image_url, output_path=None, pub_date="", ad_banner_url=None):
    """
    ফটোকার্ড জেনারেটরের মূল রাউটার:
    প্রথমে উচ্চমানের হেডলেস ব্রাউজার ইঞ্জিন ব্যবহার করে, না পেলে পিলো ফলব্যাকে যায়।
    """
    card = generate_photocard_browser(
        title, image_url, output_path=output_path, pub_date=pub_date, ad_banner_url=ad_banner_url
    )
    if not card:
        card = generate_photocard_pillow(title, image_url, output_path=output_path, pub_date=pub_date)
    return card


def post_to_facebook(title, link, photocard_path=None):
    """
    ফেসবুক পেজে সরাসরি ব্র্যান্ডেড ফটোকার্ড আপলোড করে এবং প্রথম কমেন্টে নিউজ লিংক প্রকাশ করে।
    এই পদ্ধতিতে সোশ্যাল মিডিয়া লিঙ্ক শেয়ারের চেয়ে ৩ গুণ বেশি রিচ ও এনগেজমেন্ট অর্জিত হয়।
    """
    if not FB_PAGE_ID or not FB_PAGE_ACCESS_TOKEN or FB_PAGE_ID == "YOUR_FACEBOOK_PAGE_ID":
        print("⚠️ ফেসবুক পেজ ক্রেডেনশিয়াল পাওয়া যায়নি বা সেট করা হয়নি। স্কিপ করা হচ্ছে...")
        return False

    # পোস্ট ক্যাপশন: শুধুমাত্র শিরোনাম এবং ফটোকার্ড (লিংক থাকবে ১ম কমেন্টে, যা ফেসবুক অ্যালগরিদমে সর্বোচ্চ রিচ দেয়)
    message = (
        f"{title}\n\n"
        f"#Ghatail #ঘাটাইল #টাঙ্গাইল"
    )

    try:
        import requests

        # ১. যদি লোকাল ফটোকার্ড ইমেজ থাকে, আসল ফটো হিসেবে আপলোড
        if photocard_path and os.path.exists(photocard_path):
            p_url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/photos"
            with open(photocard_path, "rb") as f:
                res = requests.post(
                    p_url,
                    files={"source": f},
                    data={
                        "caption": message,
                        "access_token": FB_PAGE_ACCESS_TOKEN
                    },
                    timeout=30
                )
            res_data = res.json()
            if res.status_code == 200 and ("id" in res_data or "post_id" in res_data):
                post_id = res_data.get("post_id") or res_data.get("id")
                print(f"🎉 ✅ ফেসবুকে ফটোকার্ড সরাসরি আপলোড সফল! Post ID: {post_id}")
                
                # পোস্টের ১ম কমেন্টে ওয়েবসাইটের নিউজ লিংক যোগ করা (অ্যালগরিদম অপ্টিমাইজেশন)
                try:
                    c_url = f"https://graph.facebook.com/v19.0/{post_id}/comments"
                    c_res = requests.post(c_url, data={
                        "message": f"🔗 সংবাদের বিস্তারিত লিংক:\n{link}\n\n📢 হোয়াটসঅ্যাপ চ্যানেলে নিয়মিত আপডেট পেতে যুক্ত থাকুন:\nhttps://whatsapp.com/channel/0029Vb4vGKFLCoX9YN0gVo1C",
                        "access_token": FB_PAGE_ACCESS_TOKEN
                    }, timeout=15)
                    c_data = c_res.json()
                    if c_res.status_code == 200 and "id" in c_data:
                        print(f"💬 কমেন্টে সংবাদের বিস্তারিত লিংক যুক্ত করা হয়েছে! Comment ID: {c_data['id']}")
                    else:
                        c_err = c_data.get("error", {}).get("message", c_res.text)
                        print(f"⚠️ কমেন্ট যোগ করতে ফেসবুক পারমিশন প্রয়োজন: {c_err}")
                except Exception as ce:
                    print(f"কমেন্ট যোগ করতে সমস্যা: {ce}")
                return True
            else:
                err_msg = res_data.get("error", {}).get("message", str(res_data))
                err_code = res_data.get("error", {}).get("code", "unknown")
                print(f"❌ ফেসবুক ফটো আপলোড প্রত্যাখ্যান করেছে [Code {err_code}]: {err_msg}")
                if err_code == 190:
                    print("💡 টিপস: ফেসবুক এক্সেস টোকেনের মেয়াদ উত্তীর্ণ হয়েছে। নতুন টোকেন পেতে 'fb_token_wizard.html' খুলুন।")
                return False

        # ২. অল্টারনেট: সাধারণ লিঙ্ক পোস্ট
        else:
            url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/feed"
            res = requests.post(
                url,
                data={
                    "message": message,
                    "link": link,
                    "access_token": FB_PAGE_ACCESS_TOKEN
                },
                timeout=20
            )
            res_data = res.json()
            if res.status_code == 200 and "id" in res_data:
                print(f"✅ ফেসবুকে লিংক পোস্ট সফল! ID: {res_data['id']}")
                return True
            else:
                print(f"❌ ফেসবুকে লিংক পোস্ট ব্যর্থ: {res_data}")
                return False

    except Exception as e:
        print(f"❌ ফেসবুকে পোস্ট করতে ব্যতিক্রমি ত্রুটি: {e}")
        return False


def post_to_twitter(title, link):
    """এক্স (টুইটার)-এ নতুন সংবাদের টুইট প্রকাশ করে (Twitter API v2)"""
    if not TWITTER_BEARER_TOKEN:
        return False

    url = "https://api.twitter.com/2/tweets"
    tweet_text = f"ব্রেকিং নিউজ: {title}\n\nবিস্তারিত পড়ুন:\n{link}\n\n#Ghatail #ঘাটাইল #টাঙ্গাইল"
    if len(tweet_text) > 280:
        short_title = title[:150] + "..."
        tweet_text = f"ব্রেকিং: {short_title}\n\n{link}\n#ঘাটাইল"

    try:
        import requests
        headers = {
            "Authorization": f"Bearer {TWITTER_BEARER_TOKEN}",
            "Content-Type": "application/json"
        }
        res = requests.post(url, headers=headers, json={"text": tweet_text}, timeout=15)
        if res.status_code in (200, 201):
            print("✅ এক্স (টুইটার)-এ সফলভাবে টুইট হয়েছে!")
            return True
    except Exception as e:
        print(f"টুইটারে পাঠাতে ত্রুটি: {e}")
    return False


def post_to_telegram(title, link, photocard_path=None):
    """টেলিগ্রাম চ্যানেলে ফটোকার্ড ও সংবাদ পুশ করে"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHANNEL_ID:
        return False

    text = (
        f"⚡ <b>{title}</b>\n\n"
        f"🔗 বিস্তারিত পড়তে ক্লিক করুন:\n{link}\n\n"
        f"📢 হোয়াটসঅ্যাপ চ্যানেল:\nhttps://whatsapp.com/channel/0029Vb4vGKFLCoX9YN0gVo1C\n\n"
        f"<i>ঘাটাইল ডট কম • বস্তুনিষ্ঠ সংবাদের বিশ্বস্ত ঠিকানা</i>"
    )

    try:
        import requests
        if photocard_path and os.path.exists(photocard_path):
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
            with open(photocard_path, "rb") as f:
                res = requests.post(
                    url,
                    data={"chat_id": TELEGRAM_CHANNEL_ID, "caption": text, "parse_mode": "HTML"},
                    files={"photo": f},
                    timeout=20
                )
            if res.status_code == 200:
                print("✅ টেলিগ্রাম চ্যানেলে ফটোকার্ডসহ পাঠানো হয়েছে!")
                return True
        else:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            res = requests.post(
                url,
                data={"chat_id": TELEGRAM_CHANNEL_ID, "text": text, "parse_mode": "HTML"},
                timeout=15
            )
            if res.status_code == 200:
                print("✅ টেলিগ্রাম চ্যানেলে বার্তা পাঠানো হয়েছে!")
                return True
    except Exception as e:
        print(f"টেলিগ্রামে পাঠাতে ত্রুটি: {e}")
    return False


def post_to_whatsapp(title, link, photocard_path=None):
    """হোয়াটসঅ্যাপ চ্যানেলে ফটোকার্ড ও সংবাদ পুশ করে (Whapi.cloud API)"""
    if not WHATSAPP_API_TOKEN or not WHATSAPP_CHANNEL_JID:
        return False

    caption = (
        f"⚡ *{title}*\n\n"
        f"🔗 বিস্তারিত পড়তে ক্লিক করুন:\n{link}\n\n"
        f"📌 _ঘাটাইল ডট কম • বস্তুনিষ্ঠ সংবাদের বিশ্বস্ত ঠিকানা_"
    )

    base_url = WHATSAPP_API_URL.rstrip("/")
    if base_url.endswith("/messages/text") or base_url.endswith("/messages/image"):
        base_url = base_url.rsplit("/messages", 1)[0]

    headers = {
        "Authorization": f"Bearer {WHATSAPP_API_TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        import requests
        # ফটোকার্ড ইমেজ থাকলে বেস৬৪ এনকোড করে /messages/image এ পাঠাই
        if photocard_path and os.path.exists(photocard_path):
            import base64
            with open(photocard_path, "rb") as img_f:
                b64_data = base64.b64encode(img_f.read()).decode("utf-8")

            payload = {
                "to": WHATSAPP_CHANNEL_JID,
                "media": f"data:image/png;base64,{b64_data}",
                "caption": caption
            }
            img_url = f"{base_url}/messages/image"
            res = requests.post(img_url, headers=headers, json=payload, timeout=30)
            if res.status_code in (200, 201):
                print("✅ হোয়াটসঅ্যাপ চ্যানেলে ফটোকার্ডসহ সফলভাবে পাঠানো হয়েছে!")
                return True
            else:
                print(f"⚠️ হোয়াটসঅ্যাপে ইমেজ পোস্ট রেসপন্স কোড: {res.status_code}, টেক্সট ট্রাই করা হচ্ছে... {res.text[:150]}")

        # ফটোকার্ড না থাকলে বা ইমেজ ফেইল করলে সাধারণ টেক্সট মেসেজ পাঠাই
        text_url = f"{base_url}/messages/text"
        res = requests.post(text_url, headers=headers, json={"to": WHATSAPP_CHANNEL_JID, "body": caption}, timeout=20)
        if res.status_code in (200, 201):
            print("✅ হোয়াটসঅ্যাপ চ্যানেলে টেক্সট বার্তা সফলভাবে পাঠানো হয়েছে!")
            return True
        else:
            print(f"❌ হোয়াটসঅ্যাপে পাঠাতে ত্রুটি: {res.status_code} - {res.text[:200]}")
    except Exception as e:
        print(f"❌ হোয়াটসঅ্যাপে পাঠাতে ব্যতিক্রমি ত্রুটি: {e}")
    return False


def run_auto_publisher(force_latest=False):
    """
    অটো-পোস্টার ইঞ্জিনের প্রধান ফাংশন
    force_latest=True দিলে ক্যাশ চেক না করে সরাসরি সর্বশেষ পোস্টটি ফটোকার্ড বানিয়ে পোস্ট করবে।
    """
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 🔍 নতুন সংবাদ অনুসন্ধান চলছে...")
    cache = load_cache()
    posts = fetch_latest_posts()

    if not posts:
        print("⚠️ ব্লগারে কোনো সংবাদ পাওয়া যায়নি।")
        return

    # ফোর্স টেস্ট মোড
    if force_latest:
        latest = posts[0]
        print(f"🧪 টেস্ট মোড: সর্বশেষ সংবাদটি প্রস্তুত করা হচ্ছে: {latest['title']}")
        photocard_path = generate_photocard(
            title=latest["title"],
            image_url=latest.get("image"),
            pub_date=latest.get("date", ""),
            ad_banner_url=latest.get("sponsor_image")
        )
        post_to_facebook(latest["title"], latest["link"], photocard_path)
        post_to_twitter(latest["title"], latest["link"])
        post_to_telegram(latest["title"], latest["link"], photocard_path)
        post_to_whatsapp(latest["title"], latest["link"], photocard_path)
        return

    # প্রথম রান হলে ক্যাশ প্রস্তুত করুন (ঐচ্ছিক: শেষ ১টি পোস্ট বাদে বাকিগুলো ক্যাশে রাখে)
    if not cache:
        print("ℹ️ প্রথমবার রান হয়েছে। বিদ্যমান সব পোস্ট ক্যাশে সংরক্ষণ করা হলো।")
        save_cache([p["link"] for p in posts])
        return

    # নতুন পোস্ট চিহ্নিত করুন
    new_posts = [p for p in posts if p["link"] not in cache]

    if not new_posts:
        print("✅ সবগুলো সংবাদ পূর্বে পোস্ট করা হয়েছে। নতুন কোনো পোস্ট নেই।")
        return

    print(f"🎉 {len(new_posts)}টি নতুন সংবাদ পাওয়া গেছে! ফটোকার্ড তৈরি ও স্বয়ংক্রিয় পাবলিশ শুরু হচ্ছে...")

    # নতুন পোস্টগুলো পাবলিশ করুন (পুরাতন থেকে নতুন ক্রমে)
    for post in reversed(new_posts):
        print(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"📢 প্রক্রিয়াকরণ চলছে: {post['title']}")
        print(f"🔗 লিঙ্ক: {post['link']}")

        # ১. ব্র্যান্ডেড ফটোকার্ড তৈরি
        photocard_path = generate_photocard(
            title=post["title"],
            image_url=post.get("image"),
            pub_date=post.get("date", ""),
            ad_banner_url=post.get("sponsor_image")
        )

        # ২. সোশ্যাল মিডিয়ায় পোস্ট
        fb_ok = post_to_facebook(post["title"], post["link"], photocard_path)
        tw_ok = post_to_twitter(post["title"], post["link"])
        tg_ok = post_to_telegram(post["title"], post["link"], photocard_path)
        wa_ok = post_to_whatsapp(post["title"], post["link"], photocard_path)

        # ৩. ক্যাশে সংরক্ষণ (অন্তত একটি প্ল্যাটফর্মে পোস্ট সফল হলে তবেই ক্যাশ করব)
        if fb_ok or wa_ok or tw_ok or tg_ok:
            cache.append(post["link"])
            save_cache(cache)
        else:
            print("⚠️ কোনো প্ল্যাটফর্মে পোস্ট সফল না হওয়ায় এই সংবাদ ক্যাশে যোগ করা হয়নি (পরের রানে পুনরায় চেষ্টা হবে)।")
        time.sleep(2)


if __name__ == "__main__":
    is_test = "--test" in sys.argv or "--force" in sys.argv
    run_auto_publisher(force_latest=is_test)
