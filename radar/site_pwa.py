"""Self-contained PWA assets for the static site build."""

from __future__ import annotations

import binascii
import hashlib
import json
import math
import struct
import zlib
from pathlib import Path

CSS = r"""
:root{color-scheme:dark;--bg:#0e1115;--surface:#151a20;--raised:#1a2027;--fg:#f1f3f5;--muted:#a5aeb9;--line:#2b333d;--accent:#edbd73;--accent-hi:#f4ca8c;--good:#a6d6b0;--radius:16px;--content:900px}
*{box-sizing:border-box}html{scroll-behavior:auto}
body{margin:0;background:var(--bg);color:var(--fg);font-family:"Noto Sans Arabic","Noto Naskh Arabic","Segoe UI",Tahoma,sans-serif;line-height:1.85}
a,button{-webkit-tap-highlight-color:transparent}a{color:inherit;text-decoration:none}a:hover{color:var(--accent-hi)}button{font:inherit}
button:focus-visible,a:focus-visible{outline:3px solid var(--accent);outline-offset:3px}button:focus:not(:focus-visible),a:focus:not(:focus-visible){outline:none}
.wrap{width:min(calc(100% - 26px),var(--content));margin:auto;padding:10px 0 48px}
.site-header{display:flex;align-items:flex-start;flex-direction:column;gap:12px;padding:8px 0 16px;border-bottom:1px solid var(--line)}
.brand{display:inline-flex;align-items:center;gap:11px;font-weight:750;letter-spacing:-.02em}.brand img{width:42px;height:42px}
.brand small{display:block;color:var(--muted);font-size:10px;letter-spacing:.13em;line-height:1.2}
.nav{display:flex;align-items:center;gap:8px;flex-wrap:wrap;width:100%}
.nav a,.nav button,.quiet-button{display:inline-flex;align-items:center;justify-content:center;min-height:44px;padding:7px 12px;border:1px solid var(--line);border-radius:999px;background:transparent;color:var(--muted);font-size:13px;cursor:pointer}
.nav a,.nav button{flex:1}
.nav a:hover,.nav button:hover,.quiet-button:hover{border-color:var(--accent);color:var(--fg)}[hidden]{display:none!important}
.page-heading{padding:22px 0 16px;max-width:720px}.kicker{margin:0 0 9px;color:var(--accent);font-size:12px;font-weight:700;letter-spacing:.06em}
h1,h2,h3,p{margin-top:0}.page-heading h1{margin:0;font-size:clamp(30px,6vw,48px);line-height:1.25;letter-spacing:-.04em}
.lede{max-width:58ch;margin:13px 0 0;color:var(--muted);font-size:15px}.update-line{margin-top:15px;color:var(--muted);font-size:12px}
.section{margin:20px 0 0}.section-heading{display:flex;align-items:baseline;justify-content:space-between;gap:12px;margin:0 0 8px}
.section-heading h2{margin:0;font-size:18px}.section-heading span{color:var(--muted);font-size:12px}
.story-list{list-style:none;padding:0;margin:0}.story{padding:20px 0;border-bottom:1px solid var(--line)}.story:first-child{border-top:1px solid var(--line)}
.story--feature{margin-bottom:8px;padding:18px;border:1px solid var(--line);border-radius:var(--radius);background:linear-gradient(135deg,var(--raised),var(--surface))}
.story-title{display:block;overflow-wrap:anywhere;font-size:clamp(18px,3vw,23px);font-weight:750;line-height:1.55;letter-spacing:-.025em}
.story--feature .story-title{font-size:clamp(22px,4vw,30px)}.original-title{margin:7px 0 0;color:var(--muted);font-size:13px;direction:auto}
.story-summary{max-width:72ch;margin:10px 0 0;color:#d1d6dc;font-size:14px;line-height:1.9}
.story-meta{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-top:12px;color:var(--muted);font-size:12px}
.tag{padding:2px 9px;border:1px solid var(--line);border-radius:999px}.score{color:var(--accent);font-weight:750}
.story-actions{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-top:13px}
.save-button,.primary-link{display:inline-flex;align-items:center;justify-content:center;min-height:44px;padding:8px 15px;border:1px solid var(--accent);border-radius:999px;background:var(--accent);color:#18130c;font-size:13px;font-weight:750;cursor:pointer}
.save-button:hover,.primary-link:hover{background:var(--accent-hi);color:#18130c}.save-button[aria-pressed="true"]{background:transparent;color:var(--accent)}.detail .save-button[aria-pressed="false"]{background:transparent;color:var(--accent);border-color:var(--line)}
.secondary-link{display:inline-flex;align-items:center;justify-content:center;min-height:44px;padding:8px 15px;border:1px solid var(--line);border-radius:999px;color:var(--fg);font-size:13px}
.save-status{min-height:1.5em;color:var(--good);font-size:12px}
.detail{padding-top:22px}.detail h1{max-width:800px;margin:5px 0 10px;font-size:clamp(26px,6vw,44px);line-height:1.4;letter-spacing:-.04em}
.detail-original{color:var(--muted);font-size:15px;direction:auto}.detail-meta{margin:14px 0 18px;padding-bottom:16px;border-bottom:1px solid var(--line);color:var(--muted);font-size:13px}
.summary-panel{padding:16px;border:1px solid var(--line);border-radius:var(--radius);background:var(--surface)}
.summary-panel h2{margin:0 0 8px;font-size:17px}.summary-panel p{margin:0;color:#e1e4e8;font-size:16px;line-height:2}
.detail-note{margin:15px 0;color:var(--muted);font-size:12px}.saved-list{list-style:none;padding:0;margin:20px 0}
.saved-item{padding:18px 0;border-bottom:1px solid var(--line)}.saved-item h2{margin:0 0 8px;font-size:18px}
.saved-item p{color:var(--muted);font-size:13px}.saved-actions{display:flex;gap:8px;flex-wrap:wrap}
.empty-state{padding:24px;border:1px dashed var(--line);border-radius:var(--radius);color:var(--muted)}
.site-footer{margin-top:48px;padding-top:18px;border-top:1px solid var(--line);color:var(--muted);font-size:12px}
.site-footer a{text-decoration:underline;text-underline-offset:3px}.network-state{color:var(--muted);font-size:11px}
@media(max-width:620px){.original-title{display:-webkit-box;-webkit-box-orient:vertical;-webkit-line-clamp:2;overflow:hidden}.detail-original{display:-webkit-box;-webkit-box-orient:vertical;-webkit-line-clamp:3;overflow:hidden}}
@media(min-width:621px){.wrap{width:min(calc(100% - 36px),var(--content));padding:18px 0 54px}.site-header{align-items:center;flex-direction:row;padding-bottom:18px}.nav{width:auto}.nav a,.nav button{flex:none}.page-heading{padding:42px 0 25px}.story--feature{padding:24px}.story{padding:20px 0}.detail{padding-top:34px}.detail h1{font-size:clamp(28px,6vw,44px)}.detail-meta{margin:18px 0 28px}.summary-panel{padding:22px 24px}}
"""

APP_JS = r"""
(() => {
  "use strict";
  const root = document.documentElement.dataset.root || "./";
  const cacheName = "tech-radar-saved-v1";
  const network = document.querySelector("[data-network-state]");
  const install = document.querySelector("[data-install]");
  function updateNetwork() {
    if (network) network.textContent = navigator.onLine ? "متصل" : "بدون إنترنت";
  }
  addEventListener("online", updateNetwork);
  addEventListener("offline", updateNetwork);
  updateNetwork();
  async function register() {
    if (!("serviceWorker" in navigator)) return;
    try { await navigator.serviceWorker.register(root + "sw.js", {scope: root}); }
    catch (_) { if (network) network.textContent = "الحفظ الأوفلاين يحتاج HTTPS"; }
  }
  function ask(message) {
    return new Promise(async (resolve, reject) => {
      try {
        const registration = await navigator.serviceWorker.ready;
        const worker = navigator.serviceWorker.controller || registration.active;
        if (!worker) throw new Error("worker unavailable");
        const channel = new MessageChannel();
        const timer = setTimeout(() => reject(new Error("timeout")), 12000);
        channel.port1.onmessage = (event) => {
          clearTimeout(timer);
          event.data && event.data.ok ? resolve(event.data) : reject(new Error("request failed"));
        };
        worker.postMessage(message, [channel.port2]);
      } catch (error) { reject(error); }
    });
  }
  function urls(button) {
    return [button.dataset.savePage, button.dataset.saveFile].filter(Boolean)
      .map((value) => new URL(value, location.href).href);
  }
  async function refreshButtons() {
    if (!("caches" in window)) return;
    try {
      const cache = await caches.open(cacheName);
      for (const button of document.querySelectorAll("[data-save-page]")) {
        const saved = await cache.match(urls(button)[0]);
        button.setAttribute("aria-pressed", saved ? "true" : "false");
        button.textContent = saved ? "محفوظ · إزالة" : "حفظ دون إنترنت";
      }
    } catch (_) {}
  }
  document.querySelectorAll("[data-save-page]").forEach((button) => {
    button.addEventListener("click", async () => {
      const saved = button.getAttribute("aria-pressed") === "true";
      const status = button.parentElement.querySelector("[data-save-status]");
      button.disabled = true;
      if (status) status.textContent = saved ? "جارٍ الحذف…" : "جارٍ حفظ الملخص والملف…";
      try {
        await ask({type: saved ? "REMOVE_STORY" : "SAVE_STORY", urls: urls(button)});
        button.setAttribute("aria-pressed", saved ? "false" : "true");
        button.textContent = saved ? "حفظ دون إنترنت" : "محفوظ · إزالة";
        if (status) status.textContent = saved ? "أزيل الحفظ من هذا الجهاز." : "الملخص وملف Markdown جاهزان دون إنترنت.";
      } catch (_) {
        if (status) status.textContent = "تعذر الحفظ. اتصل بالإنترنت ثم أعد المحاولة.";
      } finally { button.disabled = false; }
    });
  });
  async function renderSaved() {
    const list = document.querySelector("[data-saved-list]");
    if (!list || !("caches" in window)) return;
    list.replaceChildren();
    try {
      const cache = await caches.open(cacheName);
      const pages = (await cache.keys()).filter((request) => {
        const path = new URL(request.url).pathname;
        return path.includes("/stories/") && path.endsWith(".html");
      });
      if (!pages.length) {
        const empty = document.createElement("li");
        empty.className = "empty-state";
        empty.textContent = "ما محفوظ شي بعد. افتح قصة واضغط «حفظ دون إنترنت».";
        list.append(empty);
        return;
      }
      for (const request of pages) {
        const response = await cache.match(request);
        if (!response) continue;
        const savedDoc = new DOMParser().parseFromString(await response.text(), "text/html");
        const title = savedDoc.querySelector('meta[name="story-title"]')?.content || "قصة محفوظة";
        const summary = savedDoc.querySelector('meta[name="story-summary"]')?.content || "";
        const file = savedDoc.querySelector('meta[name="offline-file"]')?.content || "";
        const fileUrl = file ? new URL(file, request.url).href : "";
        const item = document.createElement("li");
        item.className = "saved-item";
        const heading = document.createElement("h2");
        const link = document.createElement("a");
        link.href = request.url;
        link.textContent = title;
        heading.append(link);
        item.append(heading);
        if (summary) {
          const excerpt = document.createElement("p");
          excerpt.textContent = summary;
          item.append(excerpt);
        }
        const actions = document.createElement("div");
        actions.className = "saved-actions";
        if (fileUrl) {
          const download = document.createElement("a");
          download.className = "secondary-link";
          download.href = fileUrl;
          download.download = "";
          download.textContent = "تنزيل ملف Markdown";
          actions.append(download);
        }
        const remove = document.createElement("button");
        remove.className = "quiet-button";
        remove.type = "button";
        remove.textContent = "إزالة من المحفوظات";
        remove.addEventListener("click", async () => {
          await ask({type: "REMOVE_STORY", urls: [request.url, fileUrl].filter(Boolean)});
          renderSaved();
        });
        actions.append(remove);
        item.append(actions);
        list.append(item);
      }
    } catch (_) {
      const empty = document.createElement("li");
      empty.className = "empty-state";
      empty.textContent = "تعذر قراءة المحفوظات على هذا المتصفح.";
      list.append(empty);
    }
  }
  const clear = document.querySelector("[data-clear-saved]");
  if (clear) clear.addEventListener("click", async () => {
    await ask({type: "CLEAR_SAVED"});
    renderSaved();
  });
  let installPrompt = null;
  addEventListener("beforeinstallprompt", (event) => {
    event.preventDefault();
    installPrompt = event;
    if (install) install.hidden = false;
  });
  if (install) install.addEventListener("click", async () => {
    if (!installPrompt) return;
    installPrompt.prompt();
    await installPrompt.userChoice;
    installPrompt = null;
    install.hidden = true;
  });
  register().then(refreshButtons);
  renderSaved();
})();
"""

SERVICE_WORKER = r"""
"use strict";
const SHELL = "tech-radar-shell-__VERSION__";
const SAVED = "tech-radar-saved-v1";
const ASSETS = [
  "./index.html", "./saved.html", "./offline.html", "./app.css", "./app.js",
  "./manifest.webmanifest", "./icons/icon.svg", "./icons/icon-192.png", "./icons/icon-512.png"
];
self.addEventListener("install", (event) => event.waitUntil(
  caches.open(SHELL).then((cache) => cache.addAll(ASSETS)).then(() => self.skipWaiting())
));
self.addEventListener("activate", (event) => event.waitUntil((async () => {
  const keys = await caches.keys();
  await Promise.all(keys.filter((key) => key.startsWith("tech-radar-shell-") && key !== SHELL)
    .map((key) => caches.delete(key)));
  await self.clients.claim();
})()));
function scoped(value) {
  const url = new URL(value, self.registration.scope);
  const scope = new URL(self.registration.scope);
  if (url.origin !== self.location.origin || !url.pathname.startsWith(scope.pathname))
    throw new Error("Only files inside this app can be saved.");
  return url;
}
async function save(urls) {
  if (!Array.isArray(urls) || !urls.length) throw new Error("No files to save.");
  const cache = await caches.open(SAVED);
  const saved = [];
  for (const value of urls) {
    const url = scoped(value);
    const response = await fetch(url.href, {cache: "reload"});
    if (!response.ok) throw new Error("File unavailable (" + response.status + ").");
    await cache.put(url.href, response.clone());
    saved.push(url.href);
  }
  return saved;
}
self.addEventListener("message", (event) => {
  const port = event.ports && event.ports[0];
  const reply = (data) => { if (port) port.postMessage(data); };
  const message = event.data || {};
  event.waitUntil((async () => {
    try {
      if (message.type === "SAVE_STORY") reply({ok: true, urls: await save(message.urls)});
      else if (message.type === "REMOVE_STORY") {
        const cache = await caches.open(SAVED);
        for (const value of message.urls || []) await cache.delete(scoped(value).href);
        reply({ok: true});
      } else if (message.type === "CLEAR_SAVED") {
        await caches.delete(SAVED);
        reply({ok: true});
      } else reply({ok: false, error: "Unknown request."});
    } catch (error) { reply({ok: false, error: error.message}); }
  })());
});
self.addEventListener("fetch", (event) => {
  const request = event.request;
  if (request.method !== "GET" || new URL(request.url).origin !== self.location.origin) return;
  event.respondWith((async () => {
    const saved = await caches.open(SAVED);
    const savedResponse = await saved.match(request);
    if (savedResponse) return savedResponse;
    const shell = await caches.open(SHELL);
    const shellResponse = await shell.match(request);
    if (shellResponse) return shellResponse;
    try { return await fetch(request); }
    catch (_) {
      if (request.mode === "navigate") {
        const url = new URL(request.url);
        const rootPath = new URL(self.registration.scope).pathname;
        const fallback = url.pathname === rootPath || url.pathname.endsWith("/index.html")
          ? "./index.html" : "./offline.html";
        return (await shell.match(new URL(fallback, self.registration.scope).href))
          || new Response("لا يوجد اتصال. افتح المحفوظات أو اتصل بالإنترنت.", {
            status: 503, headers: {"Content-Type": "text/plain; charset=utf-8"}
          });
      }
      return new Response("", {status: 504, statusText: "Offline"});
    }
  })());
});
"""


def _png_chunk(kind: bytes, payload: bytes) -> bytes:
    return (
        struct.pack(">I", len(payload))
        + kind
        + payload
        + struct.pack(">I", binascii.crc32(kind + payload) & 0xFFFFFFFF)
    )


def _icon_png(size: int) -> bytes:
    background, accent, bright = (14, 17, 21, 255), (237, 189, 115, 255), (244, 202, 140, 255)
    center = (size - 1) / 2
    radii = (size * 0.10, size * 0.22, size * 0.34)
    thickness = max(1.2, size * 0.012)
    ux = math.sqrt(0.5)
    uy = -ux
    raw = bytearray()
    for y in range(size):
        raw.append(0)
        dy = y - center
        for x in range(size):
            dx = x - center
            distance = math.hypot(dx, dy)
            color = accent if any(abs(distance - radius) <= thickness for radius in radii) else background
            projection = max(0.0, min(size * 0.35, dx * ux + dy * uy))
            if projection > size * 0.06 and math.hypot(dx - projection * ux, dy - projection * uy) <= thickness * 1.4:
                color = bright
            if distance <= size * 0.03 or math.hypot(dx - size * 0.24, dy + size * 0.24) <= size * 0.022:
                color = bright
            raw.extend(color)
    header = struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", header)
        + _png_chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + _png_chunk(b"IEND", b"")
    )


def write_assets(out: Path, version: str) -> None:
    icons = out / "icons"
    icons.mkdir(parents=True, exist_ok=True)
    (icons / "icon.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">'
        '<rect width="512" height="512" rx="112" fill="#0e1115"/>'
        '<circle cx="256" cy="256" r="174" fill="none" stroke="#edbd73" stroke-width="10" opacity=".52"/>'
        '<circle cx="256" cy="256" r="112" fill="none" stroke="#edbd73" stroke-width="9" opacity=".72"/>'
        '<circle cx="256" cy="256" r="50" fill="none" stroke="#edbd73" stroke-width="8"/>'
        '<path d="M256 256 382 130" fill="none" stroke="#f4ca8c" stroke-width="13" stroke-linecap="round"/>'
        '<circle cx="256" cy="256" r="15" fill="#f4ca8c"/><circle cx="379" cy="133" r="11" fill="#f4ca8c"/>'
        '</svg>',
        encoding="utf-8",
    )
    (icons / "icon-192.png").write_bytes(_icon_png(192))
    (icons / "icon-512.png").write_bytes(_icon_png(512))
    manifest = {
        "id": "./",
        "name": "رادار التقنيات — موجز عربي",
        "short_name": "رادار",
        "description": "موجز تقني عربي مع حفظ القصص وملفاتها للقراءة دون إنترنت.",
        "lang": "ar",
        "dir": "rtl",
        "start_url": "./",
        "scope": "./",
        "display": "standalone",
        "background_color": "#0e1115",
        "theme_color": "#0e1115",
        "icons": [
            {"src": "./icons/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
            {"src": "./icons/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"},
        ],
    }
    (out / "manifest.webmanifest").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out / "app.css").write_text(CSS, encoding="utf-8")
    (out / "app.js").write_text(APP_JS, encoding="utf-8")
    shell_assets = (
        "index.html", "saved.html", "offline.html", "manifest.webmanifest",
        "app.css", "app.js", "icons/icon.svg",
        "icons/icon-192.png", "icons/icon-512.png",
    )
    shell_content = b"".join((out / asset).read_bytes() for asset in shell_assets)
    worker_version = hashlib.sha256(
        (version + CSS + APP_JS + SERVICE_WORKER).encode("utf-8") + shell_content
    ).hexdigest()[:16]
    (out / "sw.js").write_text(
        SERVICE_WORKER.replace("__VERSION__", worker_version), encoding="utf-8"
    )
