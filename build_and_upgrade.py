import base64
import hashlib
import io
import json
import os
import re
import struct
import subprocess
from pathlib import Path
import qrcode
import qrcode.image.svg

BASE_DIR = Path(__file__).resolve().parent
ARTICLES_DIR = BASE_DIR / "articles"
IMAGES_DIR = BASE_DIR / "images"
RAW_JSON_DIR = BASE_DIR / "raw_json"

GIST_ID = "ecc8ffcc38214ae085bb2d06899db462"
DEFAULT_PASSWORD = os.environ.get("NOTE_ARCHIVE_PASSWORD", "kenhori2")
MASTER_SALT = "note_kenhori2_salt_v1"
PAGES_URL = "https://mittu-prog.github.io/note-kenhori2/"


def derive_key32(password: str, salt: str = MASTER_SALT) -> bytes:
    data = f"{salt}:{password}".encode("utf-8")
    h = hashlib.sha256(data).digest()
    for i in range(1000):
        h = hashlib.sha256(h + data).digest()
    return h


def key_verifier(key32: bytes) -> str:
    return hashlib.sha256(key32 + b":verify_v1").hexdigest()[:16]


def _rotl32(v: int, c: int) -> int:
    return ((v << c) & 0xFFFFFFFF) | (v >> (32 - c))


def _quarter_round(x: list[int], a: int, b: int, c: int, d: int):
    x[a] = (x[a] + x[b]) & 0xFFFFFFFF
    x[d] = _rotl32(x[d] ^ x[a], 16)
    x[c] = (x[c] + x[d]) & 0xFFFFFFFF
    x[b] = _rotl32(x[b] ^ x[c], 12)
    x[a] = (x[a] + x[b]) & 0xFFFFFFFF
    x[d] = _rotl32(x[d] ^ x[a], 8)
    x[c] = (x[c] + x[d]) & 0xFFFFFFFF
    x[b] = _rotl32(x[b] ^ x[c], 7)


def chacha20_xor(key32: bytes, nonce12: bytes, data: bytes) -> bytes:
    constants = (0x61707865, 0x3320646E, 0x79622D32, 0x6B206574)
    key_words = struct.unpack("<8I", key32)
    nonce_words = struct.unpack("<3I", nonce12)
    out = bytearray(len(data))
    for block_idx in range((len(data) + 63) // 64):
        state = list(constants) + list(key_words) + [block_idx] + list(nonce_words)
        working = list(state)
        for _ in range(10):
            _quarter_round(working, 0, 4, 8, 12)
            _quarter_round(working, 1, 5, 9, 13)
            _quarter_round(working, 2, 6, 10, 14)
            _quarter_round(working, 3, 7, 11, 15)
            _quarter_round(working, 0, 5, 10, 15)
            _quarter_round(working, 1, 6, 11, 12)
            _quarter_round(working, 2, 7, 8, 13)
            _quarter_round(working, 3, 4, 9, 14)
        keystream = struct.pack(
            "<16I", *((working[i] + state[i]) & 0xFFFFFFFF for i in range(16))
        )
        offset = block_idx * 64
        chunk = data[offset : offset + 64]
        for i, b in enumerate(chunk):
            out[offset + i] = b ^ keystream[i]
    return bytes(out)


def encrypt_string(plaintext: str, key32: bytes, context_id: str) -> str:
    nonce12 = hashlib.sha256(f"nonce:{context_id}".encode("utf-8")).digest()[:12]
    pt_bytes = plaintext.encode("utf-8")
    ct_bytes = chacha20_xor(key32, nonce12, pt_bytes)
    payload = nonce12 + ct_bytes
    return base64.b64encode(payload).decode("ascii")


def make_qr_svg(url: str) -> str:
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(image_factory=qrcode.image.svg.SvgPathImage)
    buf = io.BytesIO()
    img.save(buf)
    svg_str = buf.getvalue().decode("utf-8")
    svg_str = re.sub(r"<\?xml[^>]*\?>", "", svg_str).strip()
    return svg_str


def sanitize_filename(name: str, max_len: int = 60) -> str:
    cleaned = re.sub(r'[\\/:*?"<>|\r\n\t]+', "_", name).strip(" ._")
    if len(cleaned) > max_len:
        cleaned = cleaned[:max_len].rstrip(" ._")
    return cleaned or "untitled"


def get_ext_from_url(url: str) -> str:
    import urllib.parse
    parsed = urllib.parse.urlparse(url)
    path = parsed.path.lower()
    for ext in [".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"]:
        if path.endswith(ext):
            return ext
    qs = urllib.parse.parse_qs(parsed.query)
    fmt = qs.get("format", [""])[0].lower()
    if fmt in ["jpeg", "jpg"]:
        return ".jpg"
    if fmt in ["png", "gif", "webp"]:
        return f".{fmt}"
    return ".jpg"


def generate_app_js(enc_sync_cfg: str, verifier_hex: str, qr_svg: str):
    share_url = f"{PAGES_URL}#pw={DEFAULT_PASSWORD}"
    js_code = f"""/* note_kenhori2 Read-State Sync & Decryption Engine */
(function() {{
    const MASTER_SALT = {json.dumps(MASTER_SALT)};
    const KEY_VERIFIER = {json.dumps(verifier_hex)};
    const ENC_SYNC_CFG = {json.dumps(enc_sync_cfg)};
    const PAGES_URL = {json.dumps(PAGES_URL)};
    const QR_SVG_DEFAULT = {json.dumps(qr_svg)};
    const STORAGE_KEY_READ = "note_kenhori2_read_v1";
    const STORAGE_KEY_MK = "note_kenhori2_mk_v1";
    const STORAGE_KEY_PW = "note_kenhori2_pw_v1";

    // --- Pure-JS SHA-256 (works on both file:// and https://) ---
    const K256 = new Uint32Array([
        0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
        0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
        0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
        0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
        0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
        0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
        0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
        0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2
    ]);

    function rotr(n, x) {{ return (x >>> n) | (x << (32 - n)); }}

    function sha256Bytes(msgBytes) {{
        const l = msgBytes.length;
        const bitLenHi = Math.floor((l * 8) / 0x100000000);
        const bitLenLo = (l * 8) >>> 0;
        const padLen = ((l + 9 + 63) & ~63);
        const buf = new Uint8Array(padLen);
        buf.set(msgBytes);
        buf[l] = 0x80;
        const dv = new DataView(buf.buffer);
        dv.setUint32(padLen - 8, bitLenHi, false);
        dv.setUint32(padLen - 4, bitLenLo, false);

        let H0 = 0x6a09e667, H1 = 0xbb67ae85, H2 = 0x3c6ef372, H3 = 0xa54ff53a;
        let H4 = 0x510e527f, H5 = 0x9b05688c, H6 = 0x1f83d9ab, H7 = 0x5be0cd19;
        const W = new Uint32Array(64);

        for (let offset = 0; offset < padLen; offset += 64) {{
            for (let i = 0; i < 16; i++) {{
                W[i] = dv.getUint32(offset + i * 4, false);
            }}
            for (let i = 16; i < 64; i++) {{
                const s0 = rotr(7, W[i - 15]) ^ rotr(18, W[i - 15]) ^ (W[i - 15] >>> 3);
                const s1 = rotr(17, W[i - 2]) ^ rotr(19, W[i - 2]) ^ (W[i - 2] >>> 10);
                W[i] = (W[i - 16] + s0 + W[i - 7] + s1) >>> 0;
            }}
            let a = H0, b = H1, c = H2, d = H3, e = H4, f = H5, g = H6, h = H7;
            for (let i = 0; i < 64; i++) {{
                const S1 = rotr(6, e) ^ rotr(11, e) ^ rotr(25, e);
                const ch = (e & f) ^ (~e & g);
                const temp1 = (h + S1 + ch + K256[i] + W[i]) >>> 0;
                const S0 = rotr(2, a) ^ rotr(13, a) ^ rotr(22, a);
                const maj = (a & b) ^ (a & c) ^ (b & c);
                const temp2 = (S0 + maj) >>> 0;
                h = g; g = f; f = e; e = (d + temp1) >>> 0;
                d = c; c = b; b = a; a = (temp1 + temp2) >>> 0;
            }}
            H0 = (H0 + a) >>> 0; H1 = (H1 + b) >>> 0; H2 = (H2 + c) >>> 0; H3 = (H3 + d) >>> 0;
            H4 = (H4 + e) >>> 0; H5 = (H5 + f) >>> 0; H6 = (H6 + g) >>> 0; H7 = (H7 + h) >>> 0;
        }}
        const out = new Uint8Array(32);
        const outDv = new DataView(out.buffer);
        outDv.setUint32(0, H0, false); outDv.setUint32(4, H1, false);
        outDv.setUint32(8, H2, false); outDv.setUint32(12, H3, false);
        outDv.setUint32(16, H4, false); outDv.setUint32(20, H5, false);
        outDv.setUint32(24, H6, false); outDv.setUint32(28, H7, false);
        return out;
    }}

    function bytesToHex(bytes) {{
        let s = "";
        for (let i = 0; i < bytes.length; i++) {{
            s += bytes[i].toString(16).padStart(2, "0");
        }}
        return s;
    }}

    function hexToBytes(hex) {{
        const out = new Uint8Array(hex.length / 2);
        for (let i = 0; i < out.length; i++) {{
            out[i] = parseInt(hex.substr(i * 2, 2), 16);
        }}
        return out;
    }}

    function deriveKey32(password) {{
        const enc = new TextEncoder();
        const data = enc.encode(MASTER_SALT + ":" + password);
        let h = sha256Bytes(data);
        const combined = new Uint8Array(32 + data.length);
        combined.set(data, 32);
        for (let i = 0; i < 1000; i++) {{
            combined.set(h, 0);
            h = sha256Bytes(combined);
        }}
        return h;
    }}

    function verifyKey32(key32) {{
        if (!key32 || key32.length !== 32) return false;
        const suffix = new TextEncoder().encode(":verify_v1");
        const buf = new Uint8Array(32 + suffix.length);
        buf.set(key32, 0);
        buf.set(suffix, 32);
        const vHex = bytesToHex(sha256Bytes(buf)).slice(0, 16);
        return vHex === KEY_VERIFIER;
    }}

    function rotl32(v, c) {{ return ((v << c) | (v >>> (32 - c))) >>> 0; }}

    function qround(x, a, b, c, d) {{
        x[a] = (x[a] + x[b]) >>> 0; x[d] = rotl32(x[d] ^ x[a], 16);
        x[c] = (x[c] + x[d]) >>> 0; x[b] = rotl32(x[b] ^ x[c], 12);
        x[a] = (x[a] + x[b]) >>> 0; x[d] = rotl32(x[d] ^ x[a], 8);
        x[c] = (x[c] + x[d]) >>> 0; x[b] = rotl32(x[b] ^ x[c], 7);
    }}

    function chacha20Xor(key32, nonce12, dataBytes) {{
        const keyDv = new DataView(key32.buffer, key32.byteOffset, 32);
        const nonceDv = new DataView(nonce12.buffer, nonce12.byteOffset, 12);
        const state = new Uint32Array(16);
        state[0] = 0x61707865; state[1] = 0x3320646e;
        state[2] = 0x79622d32; state[3] = 0x6b206574;
        for (let i = 0; i < 8; i++) state[4 + i] = keyDv.getUint32(i * 4, true);
        for (let i = 0; i < 3; i++) state[13 + i] = nonceDv.getUint32(i * 4, true);

        const out = new Uint8Array(dataBytes.length);
        const working = new Uint32Array(16);
        const ksBytes = new Uint8Array(64);
        const ksDv = new DataView(ksBytes.buffer);
        const blocks = Math.ceil(dataBytes.length / 64);

        for (let b = 0; b < blocks; b++) {{
            state[12] = b >>> 0;
            working.set(state);
            for (let r = 0; r < 10; r++) {{
                qround(working, 0, 4, 8, 12); qround(working, 1, 5, 9, 13);
                qround(working, 2, 6, 10, 14); qround(working, 3, 7, 11, 15);
                qround(working, 0, 5, 10, 15); qround(working, 1, 6, 11, 12);
                qround(working, 2, 7, 8, 13); qround(working, 3, 4, 9, 14);
            }}
            for (let i = 0; i < 16; i++) {{
                ksDv.setUint32(i * 4, (working[i] + state[i]) >>> 0, true);
            }}
            const offset = b * 64;
            const limit = Math.min(64, dataBytes.length - offset);
            for (let i = 0; i < limit; i++) {{
                out[offset + i] = dataBytes[offset + i] ^ ksBytes[i];
            }}
        }}
        return out;
    }}

    function decryptBase64(b64, key32) {{
        const binStr = atob(b64);
        const raw = new Uint8Array(binStr.length);
        for (let i = 0; i < binStr.length; i++) raw[i] = binStr.charCodeAt(i);
        const nonce12 = raw.subarray(0, 12);
        const ct = raw.subarray(12);
        const ptBytes = chacha20Xor(key32, nonce12, ct);
        return new TextDecoder("utf-8").decode(ptBytes);
    }}

    // --- Key / Password Resolution ---
    let activeKey32 = null;
    let activePassword = null;
    let syncConfig = null;

    function loadWindowNameCache() {{
        try {{
            if (window.name && window.name.startsWith("NOTE_KH2:")) {{
                return JSON.parse(window.name.slice(9));
            }}
        }} catch (e) {{}}
        return {{}};
    }}

    function saveWindowNameCache(obj) {{
        try {{
            const cur = loadWindowNameCache();
            Object.assign(cur, obj);
            window.name = "NOTE_KH2:" + JSON.stringify(cur);
        }} catch (e) {{}}
    }}

    function tryUnlockWithPassword(pw) {{
        if (!pw) return false;
        const k = deriveKey32(pw);
        if (verifyKey32(k)) {{
            activeKey32 = k;
            activePassword = pw;
            const mkHex = bytesToHex(k);
            try {{
                localStorage.setItem(STORAGE_KEY_MK, mkHex);
                localStorage.setItem(STORAGE_KEY_PW, pw);
            }} catch (e) {{}}
            saveWindowNameCache({{ mk: mkHex, pw: pw }});
            initSyncConfig();
            return true;
        }}
        return false;
    }}

    function initSyncConfig() {{
        if (!activeKey32 || syncConfig) return;
        try {{
            const jsonStr = decryptBase64(ENC_SYNC_CFG, activeKey32);
            syncConfig = JSON.parse(jsonStr);
        }} catch (e) {{
            console.warn("Failed to decrypt sync config:", e);
        }}
    }}

    function autoResolveKey() {{
        // 1. Check URL hash #pw=...
        if (location.hash && location.hash.includes("pw=")) {{
            const m = location.hash.match(/[#&]pw=([^&]+)/);
            if (m && m[1]) {{
                const pw = decodeURIComponent(m[1]);
                if (tryUnlockWithPassword(pw)) {{
                    try {{
                        history.replaceState(null, "", location.pathname + location.search);
                    }} catch (e) {{}}
                    return true;
                }}
            }}
        }}
        // 2. Check cached Master Key in localStorage or window.name
        try {{
            const wn = loadWindowNameCache();
            const mkHex = localStorage.getItem(STORAGE_KEY_MK) || wn.mk;
            const savedPw = localStorage.getItem(STORAGE_KEY_PW) || wn.pw;
            if (mkHex && mkHex.length === 64) {{
                const k = hexToBytes(mkHex);
                if (verifyKey32(k)) {{
                    activeKey32 = k;
                    activePassword = savedPw || "";
                    saveWindowNameCache({{ mk: mkHex, pw: activePassword }});
                    initSyncConfig();
                    return true;
                }}
            }}
        }} catch (e) {{}}
        // 3. Check local_key.js (present on local PC, gitignored on GitHub Pages)
        if (window.__NOTE_LOCAL_PASS__) {{
            if (tryUnlockWithPassword(window.__NOTE_LOCAL_PASS__)) {{
                return true;
            }}
        }}
        return false;
    }}

    // --- Read State CRDT Store (localStorage + window.name + GitHub Gist) ---
    // Format: {{ [noteKey]: {{ r: 1 | 0, t: timestamp_ms }} }}
    let readState = {{}};
    let syncInProgress = false;
    let syncTimer = null;

    function loadLocalReadState() {{
        let merged = {{}};
        try {{
            const wn = loadWindowNameCache();
            if (wn.readState && typeof wn.readState === "object") {{
                merged = Object.assign({{}}, wn.readState);
            }}
        }} catch (e) {{}}
        try {{
            const raw = localStorage.getItem(STORAGE_KEY_READ);
            if (raw) {{
                const parsed = JSON.parse(raw);
                mergeStates(merged, parsed);
            }}
        }} catch (e) {{}}
        readState = merged;
    }}

    function saveLocalReadState() {{
        try {{
            localStorage.setItem(STORAGE_KEY_READ, JSON.stringify(readState));
        }} catch (e) {{}}
        saveWindowNameCache({{ readState: readState }});
    }}

    function mergeStates(target, incoming) {{
        if (!incoming || typeof incoming !== "object") return false;
        let changed = false;
        for (const [k, val] of Object.entries(incoming)) {{
            if (!val || typeof val !== "object") continue;
            const inT = Number(val.t) || 0;
            const inR = val.r ? 1 : 0;
            const cur = target[k];
            if (!cur || inT > (Number(cur.t) || 0)) {{
                if (!cur || cur.r !== inR || cur.t !== inT) {{
                    target[k] = {{ r: inR, t: inT }};
                    changed = true;
                }}
            }}
        }}
        return changed;
    }}

    function isArticleRead(key) {{
        return Boolean(readState[key] && readState[key].r === 1);
    }}

    function setArticleRead(key, isRead) {{
        if (!key) return;
        readState[key] = {{
            r: isRead ? 1 : 0,
            t: Date.now()
        }};
        saveLocalReadState();
        refreshReadUI();
        scheduleCloudSync(true);
    }}

    function toggleArticleRead(key) {{
        setArticleRead(key, !isArticleRead(key));
    }}

    function updateSyncStatusUI(state, text) {{
        const els = document.querySelectorAll(".sync-status");
        els.forEach(el => {{
            el.className = "sync-status " + (state || "");
            el.textContent = text;
        }});
    }}

    function scheduleCloudSync(pushImmediately) {{
        if (syncTimer) clearTimeout(syncTimer);
        syncTimer = setTimeout(() => syncWithGist(pushImmediately), pushImmediately ? 350 : 50);
    }}

    async function syncWithGist(forcePush) {{
        if (!syncConfig || !syncConfig.token || !syncConfig.gistId) {{
            updateSyncStatusUI("err", "🔒 パスワード未解除");
            return;
        }}
        if (syncInProgress) return;
        syncInProgress = true;
        updateSyncStatusUI("", "🔄 同期中...");

        try {{
            const resp = await fetch("https://api.github.com/gists/" + syncConfig.gistId, {{
                method: "GET",
                headers: {{
                    "Accept": "application/vnd.github+json",
                    "Authorization": "Bearer " + syncConfig.token
                }},
                cache: "no-store"
            }});
            if (!resp.ok) throw new Error("HTTP " + resp.status);
            const gistData = await resp.json();
            const fileObj = gistData.files && gistData.files["note_kenhori2_read_state.json"];
            let remoteItems = {{}};
            if (fileObj && fileObj.content) {{
                try {{
                    const parsed = JSON.parse(fileObj.content);
                    remoteItems = parsed.items || {{}};
                }} catch (e) {{}}
            }}

            const localUpdatedFromRemote = mergeStates(readState, remoteItems);
            const remoteNeedsUpdate = forcePush || mergeStates(remoteItems, readState);

            if (localUpdatedFromRemote) {{
                saveLocalReadState();
                refreshReadUI();
            }}

            if (remoteNeedsUpdate) {{
                const payload = {{
                    files: {{
                        "note_kenhori2_read_state.json": {{
                            content: JSON.stringify({{
                                version: 1,
                                updated_at: new Date().toISOString(),
                                items: readState
                            }}, null, 2)
                        }}
                    }}
                }};
                const patchResp = await fetch("https://api.github.com/gists/" + syncConfig.gistId, {{
                    method: "PATCH",
                    headers: {{
                        "Accept": "application/vnd.github+json",
                        "Authorization": "Bearer " + syncConfig.token,
                        "Content-Type": "application/json"
                    }},
                    body: JSON.stringify(payload)
                }});
                if (!patchResp.ok) throw new Error("PATCH HTTP " + patchResp.status);
            }}

            const nowStr = new Date().toLocaleTimeString("ja-JP", {{ hour: "2-digit", minute: "2-digit" }});
            updateSyncStatusUI("ok", "☁️ 同期済 (" + nowStr + ")");
        }} catch (err) {{
            console.warn("Gist sync error:", err);
            updateSyncStatusUI("err", "⚠️ オフライン (端末保存済)");
        }} finally {{
            syncInProgress = false;
        }}
    }}

    // --- UI Rendering & Decryption ---
    let currentReadFilter = "all"; // "all" | "unread" | "read"

    function unlockEncryptedElements() {{
        if (!activeKey32) return;
        const encNodes = document.querySelectorAll("[data-enc]");
        encNodes.forEach(node => {{
            const b64 = node.getAttribute("data-enc");
            if (!b64) return;
            try {{
                const html = decryptBase64(b64, activeKey32);
                node.innerHTML = html;
                node.removeAttribute("data-enc");
            }} catch (e) {{
                console.error("Decryption error:", e);
            }}
        }});
        const lockBoxes = document.querySelectorAll(".lock-box");
        lockBoxes.forEach(b => b.remove());
    }}

    function showLockScreenIfNeeded() {{
        if (activeKey32) return;
        const encNodes = document.querySelectorAll("[data-enc]");
        encNodes.forEach(node => {{
            if (node.querySelector(".lock-box")) return;
            node.innerHTML = `
                <div class="lock-box">
                    <h3>🔒 パスワード保護された記事</h3>
                    <p>記事本文の表示とPC・スマホ間の既読同期を行うにはパスワードを入力してください。<br>（一度入力するとこのブラウザに記憶されます）</p>
                    <form class="pw-form" onsubmit="return window.__noteSubmitPw(event)">
                        <input type="password" class="pw-input" placeholder="パスワードを入力..." required>
                        <button type="submit" class="pw-submit">解除</button>
                    </form>
                </div>
            `;
        }});
    }}

    window.__noteSubmitPw = function(ev) {{
        ev.preventDefault();
        const form = ev.target;
        const input = form.querySelector(".pw-input");
        const pw = (input && input.value || "").trim();
        if (tryUnlockWithPassword(pw)) {{
            unlockEncryptedElements();
            closeModal("pwModal");
            syncWithGist(false);
        }} else {{
            alert("パスワードが正しくありません。");
        }}
        return false;
    }};

    function refreshReadUI() {{
        // 1. Index page cards
        const cards = document.querySelectorAll(".card[data-key]");
        let totalCount = cards.length;
        let readCount = 0;

        cards.forEach(card => {{
            const key = card.getAttribute("data-key");
            const r = isArticleRead(key);
            if (r) readCount++;
            card.classList.toggle("is-read", r);
            card.setAttribute("data-read", r ? "1" : "0");
            const btn = card.querySelector(".check-btn");
            if (btn) {{
                btn.classList.toggle("is-read", r);
                btn.innerHTML = r
                    ? '<span class="check-icon">✓</span><span>読了済</span>'
                    : '<span class="check-icon"></span><span>未読</span>';
                btn.title = r ? "クリックで未読に戻す" : "クリックで読了にする";
            }}
        }});

        if (totalCount > 0) {{
            const unreadCount = totalCount - readCount;
            const pct = Math.round((readCount / totalCount) * 100);
            const statEl = document.getElementById("readProgressStats");
            if (statEl) {{
                statEl.innerHTML = `読了: <span class="read-num">${{readCount}}</span> / ${{totalCount}}件 (${{pct}}%) <span class="unread-num">・ 未読: ${{unreadCount}}件</span>`;
            }}
            const fillEl = document.getElementById("readProgressFill");
            if (fillEl) {{
                fillEl.style.width = pct + "%";
            }}
            const tabAll = document.getElementById("tabReadAll");
            const tabUnread = document.getElementById("tabReadUnread");
            const tabRead = document.getElementById("tabReadDone");
            if (tabAll) tabAll.textContent = `すべて (${{totalCount}})`;
            if (tabUnread) tabUnread.textContent = `未読のみ (${{unreadCount}})`;
            if (tabRead) tabRead.textContent = `読了済み (${{readCount}})`;

            if (typeof window.filterArticles === "function") {{
                window.filterArticles();
            }}
        }}

        // 2. Article page buttons
        const articleMarker = document.querySelector("[data-article-key]");
        if (articleMarker) {{
            const key = articleMarker.getAttribute("data-article-key");
            const r = isArticleRead(key);
            const topBtn = document.getElementById("topReadBtn");
            if (topBtn) {{
                topBtn.classList.toggle("is-read", r);
                topBtn.innerHTML = r
                    ? '<span class="check-icon">✓</span><span>読了済</span>'
                    : '<span class="check-icon"></span><span>未読</span>';
            }}
            const bottomBtn = document.getElementById("bottomReadBtn");
            if (bottomBtn) {{
                bottomBtn.classList.toggle("is-read", r);
                bottomBtn.innerHTML = r
                    ? '✓ 読了済み（タップで未読に戻す）'
                    : '✓ この記事を「読了」にする';
            }}
        }}
    }}

    window.setReadFilter = function(mode) {{
        currentReadFilter = mode;
        document.querySelectorAll(".read-tab").forEach(t => {{
            t.classList.toggle("active", t.getAttribute("data-mode") === mode);
        }});
        if (typeof window.filterArticles === "function") {{
            window.filterArticles();
        }}
    }};

    window.filterArticles = function() {{
        const searchEl = document.getElementById("searchInput");
        const filterEl = document.getElementById("filterSelect");
        if (!searchEl || !filterEl) return;
        const q = searchEl.value.toLowerCase();
        const f = filterEl.value;
        const cards = document.querySelectorAll(".card");
        let visible = 0;
        cards.forEach(c => {{
            const title = (c.getAttribute("data-title") || "").toLowerCase();
            const isFull = c.getAttribute("data-full") === "1";
            const src = c.getAttribute("data-source");
            const isRead = c.getAttribute("data-read") === "1";
            let show = title.includes(q);
            if (show && f === "full" && !isFull) show = false;
            if (show && f === "mem" && src !== "mem") show = false;
            if (show && f === "mag" && src !== "mag") show = false;
            if (show && currentReadFilter === "unread" && isRead) show = false;
            if (show && currentReadFilter === "read" && !isRead) show = false;
            c.style.display = show ? "flex" : "none";
            if (show) visible++;
        }});
        const countBar = document.getElementById("countBar");
        if (countBar) countBar.textContent = "表示中: " + visible + "件";
    }};

    window.sortArticles = function() {{
        const sortEl = document.getElementById("sortSelect");
        const list = document.getElementById("articleList");
        if (!sortEl || !list) return;
        const order = sortEl.value;
        const cards = Array.from(list.querySelectorAll(".card"));
        cards.sort((a, b) => {{
            if (order === "likes") {{
                return (Number(b.getAttribute("data-likes")) || 0) - (Number(a.getAttribute("data-likes")) || 0);
            }}
            const da = a.getAttribute("data-date") || "";
            const db = b.getAttribute("data-date") || "";
            return order === "asc" ? da.localeCompare(db) : db.localeCompare(da);
        }});
        cards.forEach(c => list.appendChild(c));
    }};

    window.openModal = function(id) {{
        const el = document.getElementById(id);
        if (el) el.classList.add("open");
    }};

    window.closeModal = function(id) {{
        const el = document.getElementById(id);
        if (el) el.classList.remove("open");
    }};

    window.copyShareUrl = function() {{
        const inp = document.getElementById("shareUrlInput");
        if (!inp) return;
        inp.select();
        navigator.clipboard.writeText(inp.value).then(() => {{
            const btn = document.getElementById("copyUrlBtn");
            if (btn) {{
                const orig = btn.textContent;
                btn.textContent = "コピー完了!";
                setTimeout(() => btn.textContent = orig, 1500);
            }}
        }});
    }};

    window.__noteToggleRead = function(key, ev) {{
        if (ev) {{
            ev.preventDefault();
            ev.stopPropagation();
        }}
        toggleArticleRead(key);
    }};

    window.__noteManualSync = function() {{
        if (!activeKey32) {{
            openModal("pwModal");
            return;
        }}
        syncWithGist(true);
    }};

    function injectModals() {{
        const shareUrl = PAGES_URL + (activePassword ? ("#pw=" + encodeURIComponent(activePassword)) : "");
        const modalHtml = `
            <div class="modal-backdrop" id="qrModal" onclick="if(event.target===this)closeModal('qrModal')">
                <div class="modal-card">
                    <h3>📱 スマホで開く・チェック共有</h3>
                    <p>スマホのカメラで以下のQRコードを読み取ると、PCがついていなくても全記事の閲覧と既読チェックの自動同期ができます。<br>（スマホの「ホーム画面に追加」でアプリ化もできます）</p>
                    <div class="qr-wrap">${{QR_SVG_DEFAULT}}</div>
                    <div class="url-copy-row">
                        <input type="text" id="shareUrlInput" value="${{shareUrl}}" readonly onclick="this.select()">
                        <button class="icon-btn" id="copyUrlBtn" onclick="copyShareUrl()">URLコピー</button>
                    </div>
                    <button class="pw-submit" style="width:100%" onclick="closeModal('qrModal')">閉じる</button>
                </div>
            </div>
            <div class="modal-backdrop" id="pwModal" onclick="if(event.target===this)closeModal('pwModal')">
                <div class="modal-card">
                    <h3>🔑 パスワード入力</h3>
                    <p>記事のロック解除とクラウド既読同期のためのパスワードを入力してください。</p>
                    <form class="pw-form" style="margin-bottom:14px" onsubmit="return window.__noteSubmitPw(event)">
                        <input type="password" class="pw-input" placeholder="パスワード..." required>
                        <button type="submit" class="pw-submit">解除</button>
                    </form>
                    <button class="icon-btn" onclick="closeModal('pwModal')">キャンセル</button>
                </div>
            </div>
        `;
        const wrap = document.createElement("div");
        wrap.innerHTML = modalHtml;
        document.body.appendChild(wrap);
    }}

    function init() {{
        loadLocalReadState();
        const unlocked = autoResolveKey();
        if (unlocked) {{
            unlockEncryptedElements();
        }} else {{
            showLockScreenIfNeeded();
        }}
        injectModals();
        refreshReadUI();
        if (unlocked) {{
            syncWithGist(false);
        }} else {{
            updateSyncStatusUI("err", "🔒 パスワード未入力");
        }}

        document.addEventListener("visibilitychange", () => {{
            if (document.visibilityState === "visible" && activeKey32) {{
                loadLocalReadState();
                refreshReadUI();
                syncWithGist(false);
            }}
        }});
        window.addEventListener("pageshow", () => {{
            loadLocalReadState();
            refreshReadUI();
        }});
    }}

    if (document.readyState === "loading") {{
        document.addEventListener("DOMContentLoaded", init);
    }} else {{
        init();
    }}
}})();
"""
    (BASE_DIR / "app.js").write_text(js_code, encoding="utf-8")


def process_article_html(note_data: dict, key32: bytes, prev_link: str = None, next_link: str = None) -> str:
    key = note_data.get("key", "")
    title = note_data.get("name", "無題")
    publish_full = (note_data.get("publish_at") or note_data.get("created_at") or "")[:16].replace("T", " ")
    body_html = note_data.get("body") or ""
    eyecatch_url = note_data.get("eyecatch")
    note_url = note_data.get("note_url") or f"https://note.com/kenhori2/n/{key}"
    can_read = note_data.get("can_read", False)
    remained_char = note_data.get("remained_char_num", 0) or 0
    like_count = note_data.get("like_count", 0)

    eyecatch_html = ""
    if eyecatch_url:
        ext = get_ext_from_url(eyecatch_url)
        eyecatch_rel = f"../images/{key}/eyecatch{ext}"
        eyecatch_html = f'<div class="eyecatch"><img src="{eyecatch_rel}" alt="アイキャッチ画像" loading="lazy"></div>'

    embedded_list = note_data.get("embedded_contents") or []
    embed_map = {}
    for emb in embedded_list:
        emb_key = emb.get("key")
        if emb_key:
            embed_html = emb.get("html_for_embed") or emb.get("html_for_display") or ""
            emb_url = emb.get("url") or ""
            if not embed_html and emb_url:
                embed_html = f'<div class="embed-link"><a href="{emb_url}" target="_blank" rel="noopener">{emb_url}</a></div>'
            elif emb_url:
                embed_html = f'<div class="embed-container">{embed_html}<div class="embed-source"><a href="{emb_url}" target="_blank" rel="noopener">{emb_url}</a></div></div>'
            embed_map[emb_key] = embed_html

    def replace_embed_figure(match):
        full_tag = match.group(0)
        m_key = re.search(r'embedded-content-key=["\']([^"\']+)["\']', full_tag)
        m_src = re.search(r'data-src=["\']([^"\']+)["\']', full_tag)
        if m_key and m_key.group(1) in embed_map:
            return embed_map[m_key.group(1)]
        if m_src:
            src_url = m_src.group(1)
            return f'<div class="embed-link"><a href="{src_url}" target="_blank" rel="noopener">{src_url}</a></div>'
        return full_tag

    body_html = re.sub(
        r"<figure[^>]*embedded-content-key=[^>]*>.*?</figure>",
        replace_embed_figure,
        body_html,
        flags=re.DOTALL,
    )

    img_counter = [0]

    def replace_img_src(match):
        prefix = match.group(1)
        img_url = match.group(2)
        suffix = match.group(3)
        if not img_url.startswith("http"):
            return match.group(0)
        img_counter[0] += 1
        ext = get_ext_from_url(img_url)
        url_hash = hashlib.md5(img_url.encode("utf-8")).hexdigest()[:8]
        filename = f"img_{img_counter[0]:03d}_{url_hash}{ext}"
        rel_path = f"../images/{key}/{filename}"
        return f'{prefix}{rel_path}{suffix} loading="lazy"'

    body_html = re.sub(
        r'(<img[^>]+src=["\'])([^"\']+)(["\'])',
        replace_img_src,
        body_html,
    )

    hashtags = []
    for ht in note_data.get("hashtag_notes") or []:
        tag_name = (ht.get("hashtag") or {}).get("name")
        if tag_name:
            hashtags.append(tag_name)
    tags_html = ""
    if hashtags:
        tags_spans = "".join(f'<span class="tag">{t}</span>' for t in hashtags)
        tags_html = f'<div class="tags">{tags_spans}</div>'

    paywall_notice = ""
    if remained_char > 0 and not can_read:
        paywall_notice = f"""
        <div class="paywall-warning">
            <strong>※この記事は残り {remained_char:,} 文字が有料またはプラン対象外のため未取得です。</strong><br>
            <a href="{note_url}" target="_blank" rel="noopener">noteで元記事を開く</a>
        </div>
        """

    enc_body = encrypt_string(body_html, key32, f"article:{key}")

    nav_prev = f'<a class="nav-btn" href="{prev_link}">← 前の記事</a>' if prev_link else '<span></span>'
    nav_next = f'<a class="nav-btn" href="{next_link}">次の記事 →</a>' if next_link else '<span></span>'

    html_doc = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="robots" content="noindex, nofollow, noarchive">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="theme-color" content="#2cb696">
    <title>{title} | 堀元 見 noteアーカイブ</title>
    <link rel="stylesheet" href="../app.css">
    <style>
        :root {{
            --bg: #f8f9fa;
            --card-bg: #ffffff;
            --text: #222222;
            --muted: #666666;
            --border: #e5e7eb;
            --accent: #2cb696;
            --link: #0066cc;
            --quote-bg: #f3f4f6;
        }}
        @media (prefers-color-scheme: dark) {{
            :root {{
                --bg: #121212;
                --card-bg: #1e1e1e;
                --text: #e5e7eb;
                --muted: #9ca3af;
                --border: #374151;
                --accent: #2cb696;
                --link: #60a5fa;
                --quote-bg: #262626;
            }}
        }}
        * {{ box-sizing: border-box; }}
        body {{
            margin: 0;
            padding: 0;
            background: var(--bg);
            color: var(--text);
            font-family: -apple-system, BlinkMacSystemFont, "Hiragino Kaku Gothic ProN", "Hiragino Sans", Meiryo, sans-serif;
            line-height: 1.85;
            font-size: 17px;
        }}
        .container {{
            max-width: 780px;
            margin: 0 auto;
            padding: 20px 16px 64px;
        }}
        .top-bar {{
            margin-bottom: 18px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 14px;
        }}
        .top-bar a {{
            color: var(--accent);
            text-decoration: none;
            font-weight: 600;
        }}
        .top-bar a:hover {{ text-decoration: underline; }}
        article {{
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 32px 36px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        }}
        @media (max-width: 600px) {{
            article {{ padding: 20px 16px; }}
        }}
        .eyecatch {{
            margin: -32px -36px 24px -36px;
            border-radius: 12px 12px 0 0;
            overflow: hidden;
        }}
        @media (max-width: 600px) {{
            .eyecatch {{ margin: -20px -16px 20px -16px; }}
        }}
        .eyecatch img {{
            width: 100%;
            height: auto;
            display: block;
        }}
        h1.article-title {{
            font-size: 24px;
            line-height: 1.4;
            margin: 0 0 12px 0;
        }}
        .meta {{
            color: var(--muted);
            font-size: 14px;
            margin-bottom: 24px;
            padding-bottom: 16px;
            border-bottom: 1px solid var(--border);
            display: flex;
            flex-wrap: wrap;
            gap: 14px;
            align-items: center;
        }}
        .meta a {{ color: var(--muted); }}
        .tags {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-bottom: 20px;
        }}
        .tag {{
            background: var(--quote-bg);
            color: var(--muted);
            padding: 2px 10px;
            border-radius: 999px;
            font-size: 13px;
        }}
        .article-body p {{
            margin: 0 0 1.5em 0;
            word-break: break-word;
        }}
        .article-body h2 {{
            font-size: 21px;
            margin: 2em 0 0.8em;
            padding-bottom: 6px;
            border-bottom: 2px solid var(--accent);
        }}
        .article-body h3 {{
            font-size: 18px;
            margin: 1.6em 0 0.6em;
        }}
        .article-body figure {{
            margin: 1.8em 0;
            text-align: center;
        }}
        .article-body img {{
            max-width: 100%;
            height: auto;
            border-radius: 6px;
        }}
        .article-body figcaption {{
            font-size: 13px;
            color: var(--muted);
            margin-top: 6px;
        }}
        .article-body blockquote {{
            margin: 1.5em 0;
            padding: 16px 20px;
            background: var(--quote-bg);
            border-left: 4px solid var(--accent);
            border-radius: 0 8px 8px 0;
        }}
        .article-body a {{
            color: var(--link);
            word-break: break-all;
        }}
        .embed-link, .embed-source {{
            margin: 12px 0;
            padding: 12px 16px;
            background: var(--quote-bg);
            border: 1px solid var(--border);
            border-radius: 8px;
            font-size: 14px;
        }}
        .paywall-warning {{
            margin-top: 32px;
            padding: 20px;
            background: #fff3cd;
            color: #664d03;
            border: 1px solid #ffecb5;
            border-radius: 8px;
            text-align: center;
        }}
        .footer-nav {{
            margin-top: 24px;
            display: flex;
            justify-content: space-between;
            gap: 12px;
        }}
        .nav-btn {{
            display: inline-block;
            padding: 12px 16px;
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 8px;
            color: var(--text);
            text-decoration: none;
            font-size: 14px;
            font-weight: 600;
            max-width: 48%;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}
        .nav-btn:hover {{
            border-color: var(--accent);
        }}
    </style>
</head>
<body data-article-key="{key}">
    <div class="container">
        <div class="top-bar">
            <a href="../index.html">← 記事一覧に戻る</a>
            <div class="top-bar-right">
                <span class="sync-status" onclick="window.__noteManualSync()" style="cursor:pointer" title="クリックで今すぐ同期">☁️ 同期確認中</span>
                <button type="button" id="topReadBtn" class="check-btn" onclick="window.__noteToggleRead('{key}', event)">
                    <span class="check-icon"></span><span>未読</span>
                </button>
                <a href="{note_url}" target="_blank" rel="noopener">元記事 ↗</a>
            </div>
        </div>
        <article>
            {eyecatch_html}
            <h1 class="article-title">{title}</h1>
            <div class="meta">
                <span>公開日: {publish_full}</span>
                <span>スキ: ♥ {like_count}</span>
                <span>ID: {key}</span>
            </div>
            {tags_html}
            <div class="article-body" data-enc="{enc_body}"></div>
            {paywall_notice}
            <div class="article-read-box">
                <button type="button" id="bottomReadBtn" class="article-read-btn-large" onclick="window.__noteToggleRead('{key}', event)">
                    ✓ この記事を「読了」にする
                </button>
                <span class="article-read-hint">チェック状態はPC・スマホ間で自動共有されます</span>
            </div>
        </article>
        <div class="footer-nav">
            {nav_prev}
            <a class="nav-btn" href="../index.html" style="text-align:center">一覧へ戻る</a>
            {nav_next}
        </div>
    </div>
    <script src="../local_key.js" onerror=""></script>
    <script src="../app.js"></script>
</body>
</html>
"""
    return html_doc


def build_index_html(articles_meta: list[dict]):
    rows_html = []
    full_count = sum(1 for a in articles_meta if a["is_full"])
    total_count = len(articles_meta)

    for a in articles_meta:
        badge = (
            '<span class="badge badge-full">全文保存済</span>'
            if a["is_full"]
            else '<span class="badge badge-preview">プレビューのみ</span>'
        )
        src_badge = (
            '<span class="badge badge-mem">メンバーシップ特典</span>'
            if a["in_membership_list"]
            else '<span class="badge badge-mag">マガジン収録</span>'
        )
        key = a["key"]
        rows_html.append(f"""
        <div class="card" data-key="{key}" data-read="0" data-title="{a['title'].lower()}" data-date="{a['date']}" data-likes="{a['likes']}" data-full="{'1' if a['is_full'] else '0'}" data-source="{'mem' if a['in_membership_list'] else 'mag'}">
            <div class="card-main">
                <div class="card-meta">
                    <span class="date">{a['date']}</span>
                    <span class="badge badge-read">✓ 読了済</span>
                    {src_badge}
                    {badge}
                    <span class="likes">♥ {a['likes']}</span>
                </div>
                <a class="card-title" href="articles/{a['filename']}">{a['title']}</a>
            </div>
            <div class="card-actions">
                <button type="button" class="check-btn" onclick="window.__noteToggleRead('{key}', event)">
                    <span class="check-icon"></span><span>未読</span>
                </button>
                <a class="open-btn" href="articles/{a['filename']}">読む</a>
                <a class="orig-link" href="{a['note_url']}" target="_blank" rel="noopener" title="note元記事">元記事↗</a>
            </div>
        </div>
        """)

    index_content = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="robots" content="noindex, nofollow, noarchive">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="default">
    <meta name="apple-mobile-web-app-title" content="堀元見note">
    <meta name="theme-color" content="#2cb696">
    <link rel="manifest" href="manifest.json">
    <title>堀元 見 メンバーシップ・マガジン記事一覧 ({total_count}件)</title>
    <link rel="stylesheet" href="app.css">
    <style>
        :root {{
            --bg: #f4f6f8;
            --card-bg: #ffffff;
            --text: #1f2937;
            --muted: #6b7280;
            --border: #e5e7eb;
            --accent: #2cb696;
        }}
        @media (prefers-color-scheme: dark) {{
            :root {{
                --bg: #111827;
                --card-bg: #1f2937;
                --text: #f3f4f6;
                --muted: #9ca3af;
                --border: #374151;
                --accent: #2cb696;
            }}
        }}
        * {{ box-sizing: border-box; }}
        body {{
            margin: 0;
            padding: 0;
            background: var(--bg);
            color: var(--text);
            font-family: -apple-system, BlinkMacSystemFont, "Hiragino Kaku Gothic ProN", Meiryo, sans-serif;
        }}
        header {{
            background: var(--card-bg);
            border-bottom: 1px solid var(--border);
            padding: 24px 20px;
            text-align: center;
        }}
        header h1 {{
            margin: 0 0 8px 0;
            font-size: 22px;
        }}
        header p {{
            margin: 0;
            color: var(--muted);
            font-size: 14px;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
            padding: 20px 16px 64px;
        }}
        .controls {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-bottom: 14px;
            background: var(--card-bg);
            padding: 14px;
            border-radius: 10px;
            border: 1px solid var(--border);
        }}
        .controls input[type="search"] {{
            flex: 1;
            min-width: 200px;
            padding: 10px 14px;
            border: 1px solid var(--border);
            border-radius: 6px;
            background: var(--bg);
            color: var(--text);
            font-size: 15px;
        }}
        .controls select {{
            padding: 10px 12px;
            border: 1px solid var(--border);
            border-radius: 6px;
            background: var(--bg);
            color: var(--text);
            font-size: 14px;
        }}
        .count-bar {{
            font-size: 13px;
            color: var(--muted);
            margin-bottom: 10px;
        }}
        .list {{
            display: flex;
            flex-direction: column;
            gap: 10px;
        }}
        .card {{
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 16px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 16px;
        }}
        .card:hover {{
            border-color: var(--accent);
        }}
        .card-main {{
            flex: 1;
            min-width: 0;
        }}
        .card-meta {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            align-items: center;
            font-size: 13px;
            color: var(--muted);
            margin-bottom: 6px;
        }}
        .card-title {{
            font-size: 17px;
            font-weight: 600;
            color: var(--text);
            text-decoration: none;
            display: block;
            line-height: 1.4;
        }}
        .card-title:hover {{
            color: var(--accent);
        }}
        .badge {{
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
        }}
        .badge-full {{ background: #d1fae5; color: #065f46; }}
        .badge-preview {{ background: #fef3c7; color: #92400e; }}
        .badge-mem {{ background: #dbeafe; color: #1e40af; }}
        .badge-mag {{ background: #f3e8ff; color: #6b21a8; }}
        .card-actions {{
            display: flex;
            gap: 8px;
            align-items: center;
            flex-shrink: 0;
        }}
        .open-btn {{
            background: var(--accent);
            color: #fff;
            text-decoration: none;
            padding: 8px 16px;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 600;
        }}
        .orig-link {{
            color: var(--muted);
            text-decoration: none;
            font-size: 12px;
            padding: 6px 8px;
        }}
    </style>
</head>
<body>
    <header>
        <h1>「堀元見の炎上するから有料で書く話」アーカイブ</h1>
        <p>保存記事数: {total_count}件 （うち全文保存: {full_count}件）</p>
    </header>
    <div class="container">
        <div class="dashboard-bar">
            <div class="dashboard-top">
                <div class="progress-stats" id="readProgressStats">
                    読了: <span class="read-num">0</span> / {total_count}件 (0%) <span class="unread-num">・ 未読: {total_count}件</span>
                </div>
                <div class="sync-controls">
                    <span class="sync-status" onclick="window.__noteManualSync()" style="cursor:pointer" title="クリックで今すぐ同期">☁️ 同期確認中...</span>
                    <button type="button" class="icon-btn" onclick="window.__noteManualSync()">🔄 同期</button>
                    <button type="button" class="icon-btn" onclick="openModal('qrModal')">📱 スマホで開く / QR</button>
                </div>
            </div>
            <div class="progress-track">
                <div class="progress-fill" id="readProgressFill"></div>
            </div>
        </div>

        <div class="read-tabs">
            <div class="read-tab active" id="tabReadAll" data-mode="all" onclick="setReadFilter('all')">すべて ({total_count})</div>
            <div class="read-tab" id="tabReadUnread" data-mode="unread" onclick="setReadFilter('unread')">未読のみ ({total_count})</div>
            <div class="read-tab" id="tabReadDone" data-mode="read" onclick="setReadFilter('read')">読了済み (0)</div>
        </div>

        <div class="controls">
            <input type="search" id="searchInput" placeholder="タイトルで検索..." oninput="filterArticles()">
            <select id="filterSelect" onchange="filterArticles()">
                <option value="all">すべての種別 ({total_count}件)</option>
                <option value="mem">メンバーシップ特典のみ</option>
                <option value="mag">マガジン収録のみ</option>
            </select>
            <select id="sortSelect" onchange="sortArticles()">
                <option value="desc">新しい順</option>
                <option value="asc">古い順</option>
                <option value="likes">スキが多い順</option>
            </select>
        </div>
        <div class="count-bar" id="countBar">表示中: {total_count}件</div>
        <div class="list" id="articleList">
            {''.join(rows_html)}
        </div>
    </div>
    <script src="local_key.js" onerror=""></script>
    <script src="app.js"></script>
</body>
</html>
"""
    (BASE_DIR / "index.html").write_text(index_content, encoding="utf-8")


def main():
    token = subprocess.check_output(["gh", "auth", "token"], text=True).strip()
    key32 = derive_key32(DEFAULT_PASSWORD)
    verifier_hex = key_verifier(key32)

    sync_cfg_json = json.dumps({"gistId": GIST_ID, "token": token})
    enc_sync_cfg = encrypt_string(sync_cfg_json, key32, "sync_config_v1")

    share_url = f"{PAGES_URL}#pw={DEFAULT_PASSWORD}"
    qr_svg = make_qr_svg(share_url)

    # Write local_key.js (gitignored so local PC unlocks with zero prompts)
    (BASE_DIR / "local_key.js").write_text(
        f'window.__NOTE_LOCAL_PASS__ = {json.dumps(DEFAULT_PASSWORD)};\n',
        encoding="utf-8",
    )

    generate_app_js(enc_sync_cfg, verifier_hex, qr_svg)

    # Read existing index.html to preserve membership vs magazine source mapping
    existing_index = (BASE_DIR / "index.html").read_text(encoding="utf-8") if (BASE_DIR / "index.html").exists() else ""
    mem_keys = set()
    for m in re.finditer(r'data-source="mem"[^>]*>.*?articles/\d{4}-\d{2}-\d{2}_(n[a-z0-9]+)_', existing_index, flags=re.DOTALL):
        mem_keys.add(m.group(1))

    # Collect target keys from existing articles folder (or raw_json)
    existing_article_files = list(ARTICLES_DIR.glob("*.html"))
    target_keys = set()
    for f in existing_article_files:
        m = re.match(r"^\d{4}-\d{2}-\d{2}_(n[a-z0-9]+)_", f.name)
        if m:
            target_keys.add(m.group(1))

    notes_detail = []
    for raw_file in RAW_JSON_DIR.glob("*.json"):
        key = raw_file.stem
        if target_keys and key not in target_keys:
            continue
        try:
            nd = json.loads(raw_file.read_text(encoding="utf-8"))
            if nd and nd.get("key"):
                notes_detail.append(nd)
        except Exception:
            pass

    notes_detail.sort(
        key=lambda x: (x.get("publish_at") or x.get("created_at") or ""),
        reverse=True,
    )

    filenames = []
    for nd in notes_detail:
        key = nd.get("key", "")
        date_str = (nd.get("publish_at") or nd.get("created_at") or "0000-00-00")[:10]
        safe_title = sanitize_filename(nd.get("name", "無題"))
        filenames.append(f"{date_str}_{key}_{safe_title}.html")

    articles_meta = []
    for i, nd in enumerate(notes_detail):
        key = nd.get("key", "")
        fname = filenames[i]
        prev_link = filenames[i + 1] if i + 1 < len(filenames) else None
        next_link = filenames[i - 1] if i - 1 >= 0 else None

        html_doc = process_article_html(nd, key32, prev_link=prev_link, next_link=next_link)
        (ARTICLES_DIR / fname).write_text(html_doc, encoding="utf-8")

        is_full = bool(nd.get("can_read") or (nd.get("remained_char_num") in (0, None) and nd.get("body")))
        in_mem = (key in mem_keys) if mem_keys else bool(nd.get("circle_plans"))
        articles_meta.append({
            "key": key,
            "title": nd.get("name", "無題"),
            "date": (nd.get("publish_at") or nd.get("created_at") or "")[:10],
            "likes": nd.get("like_count", 0),
            "filename": fname,
            "note_url": nd.get("note_url") or f"https://note.com/kenhori2/n/{key}",
            "is_full": is_full,
            "in_membership_list": in_mem,
        })

    build_index_html(articles_meta)
    print(f"[OK] Upgraded {len(articles_meta)} articles and index.html successfully!")


if __name__ == "__main__":
    main()
