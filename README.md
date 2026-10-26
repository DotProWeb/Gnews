# ঘাটাইল ডট কম — সোশ্যাল মিডিয়া অটো-পাবলিশার (Ghatail.com Auto-Publisher)

[![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-Automated-blue?logo=github-actions)](https://github.com/DotProWeb/Gnews/actions)
[![Facebook](https://img.shields.io/badge/Facebook-Page%20API-1877F2?logo=facebook)](https://developers.facebook.com)
[![WhatsApp](https://img.shields.io/badge/WhatsApp-Channel%20API-25D366?logo=whatsapp)](https://whapi.cloud)

Blogger-এ নতুন সংবাদ publish হওয়ার সাথে সাথে **স্বয়ংক্রিয়ভাবে** branded HD ফটোকার্ড তৈরি করে **Facebook Page**, **WhatsApp Channel**, **Telegram** ও **X (Twitter)**-এ post করার পূর্ণাঙ্গ auto-publishing engine।

---

## 📋 সূচিপত্র

1. [কীভাবে কাজ করে](#-কীভাবে-কাজ-করে)
2. [ফিচারসমূহ](#-ফিচারসমূহ)
3. [ফাইল স্ট্রাকচার](#-ফাইল-স্ট্রাকচার)
4. [GitHub Actions সেটআপ](#-github-actions-সেটআপ)
5. [GitHub Secrets কনফিগারেশন](#-github-secrets-কনফিগারেশন)
6. [Facebook Page API সেটআপ](#-facebook-page-api-সেটআপ)
7. [WhatsApp Channel সেটআপ](#-whatsapp-channel-সেটআপ)
8. [Telegram Bot সেটআপ](#-telegram-bot-সেটআপ)
9. [X / Twitter সেটআপ](#-x--twitter-সেটআপ)
10. [লোকাল ডেভেলপমেন্ট](#-লোকাল-ডেভেলপমেন্ট)
11. [নিরাপত্তা](#-নিরাপত্তা)
12. [ট্রাবলশুটিং](#-ট্রাবলশুটিং)

---

## 🔍 কীভাবে কাজ করে

```
Blogger-এ নতুন পোস্ট Publish
           |
           v
  RSS Feed আপডেট হয়
  (ghataildotcom.blogspot.com/feeds/posts/default?alt=rss)
           |
           v
  GitHub Actions — প্রতি ১০ মিনিটে RSS চেক করে
           |
           v
  নতুন পোস্ট শনাক্ত হলে — HD ফটোকার্ড তৈরি (1200x960)
           |
           v
  +---------------------------------+
  | Facebook Page  (ফটোকার্ড + লিঙ্ক comment)  |
  | WhatsApp Channel (ফটোকার্ড + caption)      |
  | Telegram Channel (ফটোকার্ড + HTML বার্তা)  |
  | X / Twitter      (text tweet + লিঙ্ক)      |
  +---------------------------------+
           |
           v
  posted_cache.json আপডেট — duplicate পোস্ট হবে না
```

---

## 🌟 ফিচারসমূহ

- **HD ফটোকার্ড** — 1200×960 resolution-এ বাংলা headline, logo ও ad banner সহ
- **সম্পূর্ণ স্বয়ংক্রিয়** — Blogger-এ post করুন, বাকি কাজ automatically হয়
- **Duplicate সুরক্ষা** — `posted_cache.json` দ্বারা একই খবর একাধিকবার post হয় না
- **বিজ্ঞাপন ফিল্টার** — `ফটোকার্ড-বিজ্ঞাপন` label-এর post social media-তে যায় না
- **সিকিউর** — সকল API token GitHub Secrets-এ, কোডে কোনো hardcoded credential নেই
- **Multi-platform** — Facebook, WhatsApp, Telegram, X/Twitter একসাথে

---

## 📁 ফাইল স্ট্রাকচার

```
Gnews/
├── .github/
│   └── workflows/
│       └── autopost.yml        # GitHub Actions workflow (প্রতি ১০ মিনিট)
├── autopost.py                 # মূল auto-publisher script
├── photocard_template.html     # HD ফটোকার্ড HTML template
├── posted_cache.json           # Post history cache (auto-updated by workflow)
├── logo.png                    # Brand logo (ফটোকার্ডে ব্যবহৃত)
├── .env                        # লোকাল credentials (gitignored — never committed)
├── .gitignore                  # Sensitive ফাইল GitHub থেকে block করে
└── README.md                   # এই documentation
```

---

## ⚙️ GitHub Actions সেটআপ

Workflow সংজ্ঞায়িত আছে `.github/workflows/autopost.yml`-এ।

### Workflow Trigger

```yaml
on:
  schedule:
    - cron: '*/10 * * * *'   # প্রতি ১০ মিনিটে automatically চলে
  workflow_dispatch:           # GitHub UI থেকে manually run করা যায়
```

### Manually Run করতে

1. **[github.com/DotProWeb/Gnews/actions](https://github.com/DotProWeb/Gnews/actions)** এ যান
2. **Actions** tab → **"Auto Publish News to Social Media"** select করুন
3. **"Run workflow"** button click করুন → **"Run workflow"** confirm করুন

### Test Mode (সর্বশেষ পোস্টটি force করে পাঠাবে)

```bash
python autopost.py --test
# অথবা
python autopost.py --force
```

---

## 🔐 GitHub Secrets কনফিগারেশন

> **সতর্কতা:** সকল API token অবশ্যই GitHub Secrets-এ রাখতে হবে। কোডে সরাসরি বসানো নিষিদ্ধ।

### Secrets যোগ করার পদ্ধতি

**[Settings > Secrets > Actions](https://github.com/DotProWeb/Gnews/settings/secrets/actions)** এ গিয়ে **"New repository secret"** click করুন:

### সকল Secrets-এর তালিকা

| Secret নাম | Platform | প্রয়োজনীয়তা | কোথায় পাবেন |
|---|---|---|---|
| `FB_PAGE_ID` | Facebook | আবশ্যক | Facebook Page → About |
| `FB_PAGE_ACCESS_TOKEN` | Facebook | আবশ্যক | [Graph API Explorer](https://developers.facebook.com/tools/explorer/) |
| `WHATSAPP_API_TOKEN` | WhatsApp | আবশ্যক | [app.whapi.cloud](https://app.whapi.cloud) Dashboard |
| `WHATSAPP_CHANNEL_JID` | WhatsApp | আবশ্যক | Whapi.cloud → Channel Settings |
| `TELEGRAM_BOT_TOKEN` | Telegram | ঐচ্ছিক | [@BotFather](https://t.me/BotFather) |
| `TELEGRAM_CHANNEL_ID` | Telegram | ঐচ্ছিক | Channel username বা numeric ID |
| `TWITTER_BEARER_TOKEN` | X/Twitter | ঐচ্ছিক | [developer.twitter.com](https://developer.twitter.com) |

---

## 📘 Facebook Page API সেটআপ

### ধাপ ১: Facebook Developer App তৈরি

1. **[developers.facebook.com](https://developers.facebook.com)** → লগইন করুন
2. **My Apps** → **Create App** → **"Business"** type select করুন
3. App নাম দিন: `Ghatail Auto Publisher` → **Create App**

### ধাপ ২: Page Access Token সংগ্রহ

1. **[Graph API Explorer](https://developers.facebook.com/tools/explorer/)** ওপেন করুন
2. Dropdown থেকে আপনার App select করুন
3. **"Generate Access Token"** click করুন
4. এই Permissions যোগ করুন:
   - `pages_manage_posts`
   - `pages_read_engagement`
5. **Generate Access Token** → Facebook login → আপনার Page select করুন
6. পাওয়া token → GitHub Secret **`FB_PAGE_ACCESS_TOKEN`**-এ paste করুন

### ধাপ ৩: Page ID বের করুন

- Facebook Page → **About** section-এ Page ID দেখুন
- অথবা Graph Explorer-এ: `GET /me?fields=id,name` run করুন
- পাওয়া ID → GitHub Secret **`FB_PAGE_ID`**-এ paste করুন

### Token মেয়াদ বাড়ানো (Long-Lived Token — ৬০ দিন)

প্রজেক্টের **`fb_token_wizard.html`** ব্রাউজারে খুলুন — এটি automatically long-lived token তৈরি করে দেয়।

> **নোট:** Facebook Access Token প্রতি ৬০ দিনে মেয়াদোত্তীর্ণ হয়। মেয়াদ শেষ হলে error code `190` দেখাবে — তখন নতুন token তৈরি করে GitHub Secret আপডেট করুন।

---

## 📱 WhatsApp Channel সেটআপ

আমরা [Whapi.cloud](https://whapi.cloud) gateway ব্যবহার করি।

### ধাপ ১: Whapi.cloud Account তৈরি

1. **[app.whapi.cloud](https://app.whapi.cloud)** → Free account তৈরি করুন
2. **"Create Channel"** button click করুন
3. আপনার WhatsApp number connect করতে **QR Code** scan করুন:
   - WhatsApp App → **Linked Devices** → **Link a Device** → QR scan করুন
4. Dashboard-এ **"Connected"** দেখালে সফল

### ধাপ ২: API Token সংগ্রহ

1. Dashboard → **API** section
2. **API Token** copy করুন → GitHub Secret **`WHATSAPP_API_TOKEN`**-এ paste করুন

### ধাপ ৩: Channel JID সংগ্রহ

Channel JID format: `120363xxxxxxxxxx@newsletter`

```
GET https://gate.whapi.cloud/newsletters
Authorization: Bearer {YOUR_API_TOKEN}
```

পাওয়া JID → GitHub Secret **`WHATSAPP_CHANNEL_JID`**-এ paste করুন

### নতুন WhatsApp Channel তৈরি করতে

1. WhatsApp App → **Updates** tab → **+** icon → **New Channel**
2. নাম, বিবরণ ও আইকন দিন → Channel তৈরি করুন
3. Whapi.cloud dashboard থেকে নতুন channel-এর JID নিন

---

## 📨 Telegram Bot সেটআপ

### ধাপ ১: Bot তৈরি

1. Telegram-এ **[@BotFather](https://t.me/BotFather)** → `/newbot` পাঠান
2. Bot-এর নাম দিন → username দিন (bot-এ শেষ হতে হবে)
3. পাওয়া **HTTP API Token** → GitHub Secret **`TELEGRAM_BOT_TOKEN`**-এ paste করুন

### ধাপ ২: Channel-এ Bot যোগ করুন

1. আপনার Telegram Channel-এ bot-কে **Admin** বানান
2. Channel-এর username (যেমন: `@ghatail_news`) → GitHub Secret **`TELEGRAM_CHANNEL_ID`**-এ paste করুন

---

## 🐦 X / Twitter সেটআপ

1. **[developer.twitter.com](https://developer.twitter.com)** → Developer account apply করুন
2. **Dashboard** → **Projects & Apps** → **New App** তৈরি করুন
3. **Keys and Tokens** → **Bearer Token** copy করুন
4. GitHub Secret **`TWITTER_BEARER_TOKEN`**-এ paste করুন

---

## 💻 লোকাল ডেভেলপমেন্ট

`.env` ফাইলে আপনার credentials রাখুন (এটি gitignored — GitHub-এ যাবে না):

```env
# Facebook
FB_PAGE_ID=আপনার_পেজ_আইডি
FB_PAGE_ACCESS_TOKEN=আপনার_টোকেন

# WhatsApp
WHATSAPP_API_URL=https://gate.whapi.cloud
WHATSAPP_API_TOKEN=আপনার_হোয়াটসঅ্যাপ_টোকেন
WHATSAPP_CHANNEL_JID=আপনার_চ্যানেল@newsletter

# Telegram (optional)
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHANNEL_ID=

# Twitter (optional)
TWITTER_BEARER_TOKEN=
```

Test run করতে:

```bash
# Windows PowerShell
Get-Content .env | ForEach-Object {
    if ($_ -match '^([^#][^=]*)=(.*)$') {
        [System.Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim())
    }
}
python autopost.py --test
```

---

## 🔒 নিরাপত্তা

| সুরক্ষা ব্যবস্থা | অবস্থা |
|---|---|
| কোডে কোনো hardcoded token নেই | ✅ |
| সকল secret GitHub Secrets-এ | ✅ |
| `.gitignore` দিয়ে `.env` ব্লক | ✅ |
| Workflow minimum permissions | ✅ |

**Secrets আপডেট করুন:**
[https://github.com/DotProWeb/Gnews/settings/secrets/actions](https://github.com/DotProWeb/Gnews/settings/secrets/actions)

---

## 🛠️ ট্রাবলশুটিং

### Facebook token মেয়াদ শেষ (Code 190)
`fb_token_wizard.html` দিয়ে নতুন token তৈরি করুন → GitHub Secret আপডেট করুন।

### WhatsApp 401 Error
`WHATSAPP_API_TOKEN` মেয়াদোত্তীর্ণ। [app.whapi.cloud](https://app.whapi.cloud) থেকে regenerate করুন।

### WhatsApp 404 Error
`WHATSAPP_CHANNEL_JID` ভুল। Dashboard থেকে সঠিক JID নিন।

### একই পোস্ট বারবার যাচ্ছে
`posted_cache.json` reset করুন:
```bash
echo [] > posted_cache.json
git add posted_cache.json && git commit -m "Reset cache" && git push
```

### GitHub Actions চলছে না
[Actions tab](https://github.com/DotProWeb/Gnews/actions) → Workflow enable আছে কিনা দেখুন।

---

## 📞 সাপোর্ট

- **ওয়েবসাইট:** [ghatail.com](https://ghatail.com)
- **WhatsApp Channel:** [whatsapp.com/channel/0029Vb4vGKFLCoX9YN0gVo1C](https://whatsapp.com/channel/0029Vb4vGKFLCoX9YN0gVo1C)
- **Phone:** 01713-328802

---

*সর্বশেষ আপডেট: অক্টোবর ২০২৬ | ঘাটাইল ডট কম — বস্তুনিষ্ঠ সংবাদের বিশ্বস্ত ঠিকানা*
