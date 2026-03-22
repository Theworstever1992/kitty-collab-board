# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in this repository, please open a GitHub issue
with the label **security** or contact the repository owner directly. Do **not** include
exploit details in a public issue.

---

## Security Incident Report — February / March 2026

### What happened

A **malicious obfuscated exec-based backdoor** was appended to `meow.py` in commit
`53e4b84` on **Feb 27, 2026** and remained undetected until **Mar 20, 2026**, when it
was identified and removed in commit `cab6880`.

The payload was a **Solana cryptocurrency wallet drainer** that silently downloaded a
second-stage JavaScript exploit from a remote C2 server and executed it via a copy of
Node.js it downloaded itself.

---

### Origin — Exact Forensic Details

| Field | Value |
|-------|-------|
| **Commit SHA** | `53e4b84111280a206046ddb97301f0bebcc73018` |
| **Date** | Fri Feb 27, 2026 at 10:01 AM MST |
| **Commit message** | "🚀 Add GitHub Action for Docker publishing to GHCR" |
| **Author (git)** | `Avery <avery@example.com>` |
| **Committer (git)** | `Prettykittyboi` (GitHub account `Theworstever1992`) |
| **GPG signed** | No |

The author identity `Avery <avery@example.com>` is **fake**. The `@example.com` domain
is reserved by RFC 2606 and is never used by real people. The commit was disguised as a
legitimate CI/CD addition; the malicious lines were appended **after** the
`if __name__ == "__main__":` guard, where they could easily be overlooked in review.

The same fake author made three commits in ~28 minutes on the same day:

| Time (MST) | SHA | Description |
|------------|-----|-------------|
| 09:33 | `87d18ed` | Added `windows/meowzon.spec` (PyInstaller spec) |
| 09:56 | `8c77509` | Added Dockerfile / docker-compose.yml |
| **10:01** | **`53e4b84`** | **Injected malicious payload into `meow.py`** |

---

### What the Malicious Code Did

The 9-line injection encoded a 438-line Python program using three layers of obfuscation:

1. **XOR cipher** (key `134`) applied byte-by-byte
2. **zlib compression** of the XOR'd bytes
3. **base64 encoding** of the compressed data
4. **`exec(compile(…))`** to execute at import time, silently

When decoded, the payload:

| Stage | Description |
|-------|-------------|
| **Delay** | Waited 10 seconds after import to evade sandbox timing checks |
| **Geofencing** | Skipped execution on Russian-locale systems (checks `LANG`, `LANGUAGE`, `LC_ALL`) |
| **Throttle** | Used `~/init.json` to run at most once every 2 days per machine |
| **C2 channel** | Polled multiple Solana RPC endpoints (`api.mainnet-beta.solana.com`, `solana-rpc.publicnode.com`, `go.getblock.us/…`, and 5 others) |
| **Runtime download** | Silently downloaded Node.js v22.9.0 from `nodejs.org` (cross-platform: Windows x64/x86, macOS arm64/x64, Linux arm64/x64) |
| **Stage 2 fetch** | Made an HTTP request to a C2 URL (obtained from Solana transaction memos), receiving an AES `secretKey` + `IV` in HTTP response headers |
| **Execution** | Wrote `i.js` next to `meow.py` containing `eval(atob('<base64 stage-2>'))` and ran it via Node.js with stdout/stderr suppressed and `CREATE_NO_WINDOW` on Windows |

Comments inside the payload were written in **Russian**, consistent with known
geofencing behaviour in Russian-speaking malware families.

---

### Impact Assessment

| Question | Answer |
|----------|--------|
| Was the backdoor ever executed? | Unknown — depends on whether anyone ran `python3 meow.py` between Feb 27 – Mar 20, 2026 |
| Was any data exfiltrated? | Unknown |
| Were credentials exposed? | No hardcoded credentials in the repository itself |
| Is the current codebase clean? | **Yes** — verified by `scripts/security_scan.py` |

---

### What You Should Do If You Ran the Code Before Commit `cab6880`

1. **Rotate secrets** accessible on the affected machine: API keys, SSH keys,
   wallet seed phrases, cloud credentials.
2. **Audit outbound connections** for traffic to Solana RPC nodes and `nodejs.org`.
3. **Remove unexpected Node.js installs** in your home directory or temp folders.
4. **Check for new cron jobs, startup items, or background processes**.
5. **Look for `i.js` or `~/init.json`** created by the payload.

---

## Is My Device Compromised?

**Short answer:** possibly yes, if you ran `python3 meow.py` (or any script that
imports it) on a machine while commit `53e4b84` was present — i.e. between
**Feb 27, 2026** and **Mar 20, 2026**.

The payload only fully activated when all three conditions were true:

1. `meow.py` was executed (not just downloaded)
2. The system locale was **not** Russian
3. The file `~/init.json` did not exist from a previous run in the last 2 days

If you did run `meow.py` on a non-Russian-locale machine during that window,
treat the device as **potentially compromised** until you complete the checks below.

---

### Indicators of Compromise (IoCs)

Look for the following artefacts the payload would have left behind:

#### Files

| Path | Meaning |
|------|---------|
| `~/init.json` | Throttle file — **strong evidence** the payload ran |
| `i.js` (next to `meow.py`) | Stage-2 JS execution wrapper — **strong evidence** |
| `~/.node-runtime/` or `/tmp/node-*/` | Secretly downloaded Node.js install |
| Any `.zip` / `.tar.gz` / `.tar.xz` containing `node-v22.9.0` in `~/` or `/tmp/` | Node.js download artefact |

**Quick check (macOS / Linux):**

```bash
ls -la ~/init.json 2>/dev/null && echo "FOUND init.json - payload likely ran"
find ~ /tmp -name 'i.js' 2>/dev/null
find ~ /tmp -name 'node-v22.9.0*' 2>/dev/null
ls -la ~/.node-runtime/ 2>/dev/null
```

**Quick check (Windows PowerShell):**

```powershell
Test-Path "$env:USERPROFILE\init.json"   # True = payload likely ran
Get-ChildItem $env:USERPROFILE, $env:TEMP -Filter 'i.js'       -Recurse -ErrorAction SilentlyContinue
Get-ChildItem $env:USERPROFILE, $env:TEMP -Filter 'node-v22.9.0*' -Recurse -ErrorAction SilentlyContinue
```

#### Network connections

The payload connected to Solana RPC endpoints and, if it received a C2 URL,
made an outbound HTTPS request to that URL. Check your firewall/router logs for
connections to:

```
api.mainnet-beta.solana.com
solana-mainnet.gateway.tatum.io
go.getblock.us
solana-rpc.publicnode.com
api.blockeden.xyz
solana.drpc.org
solana.leorpc.com
solana.api.onfinality.io
solana.api.pocket.network
nodejs.org  (for the Node.js download)
```

**Quick check — recent DNS lookups (macOS):**

```bash
log show --predicate 'process == "mDNSResponder"' --last 30d 2>/dev/null \
  | grep -E 'solana|blockeden|getblock|leorpc|onfinality|pocket\.network|nodejs\.org'
```

**Quick check — recent DNS lookups (Linux):**

```bash
grep -rE 'solana|blockeden|getblock|leorpc|onfinality|pocket\.network|nodejs\.org' \
  /var/log/syslog /var/log/messages /var/log/daemon.log 2>/dev/null | tail -20
```

#### Processes

The payload launched `node i.js` in a hidden window (Windows: `CREATE_NO_WINDOW`).
Check for unexpected `node` processes or recent `node` history:

```bash
# macOS / Linux — check if node is installed where it shouldn't be
which node 2>/dev/null
find ~ /tmp -name 'node' -type f 2>/dev/null

# History check
grep -E '\bnode\b|\bi\.js\b' ~/.bash_history ~/.zsh_history 2>/dev/null
```

---

### What to Do If You Find Any IoC

1. **Disconnect the device from the network** immediately.
2. **Rotate every secret** that was accessible on that machine:
   - SSH private keys → revoke from GitHub/GitLab, generate new ones
   - API tokens, `.env` files, `~/.aws/credentials`, `~/.config/gcloud/`
   - Browser-saved passwords / session cookies
   - Cryptocurrency wallet seed phrases (assume fully drained)
3. **Preserve the evidence** (copy `~/init.json`, `i.js`, any Node.js artefacts)
   before deleting them, in case you want to file a report.
4. **Delete the artefacts:**
   ```bash
   rm -f ~/init.json
   find ~ -name 'i.js' -delete
   rm -rf ~/.node-runtime/ /tmp/node-*/
   ```
5. **Audit recent activity**: check auth logs, browser history, and any cloud
   provider access logs for the Feb 27 – Mar 20 window.
6. **Rebuild the machine** if the IoCs are confirmed, or if you depend on the
   machine for high-value secrets (wallets, production credentials).  A
   compromised machine cannot be fully trusted after Stage-2 JS execution.

---

### What to Do If You Find No IoC

If none of the files or connections above are present, the most likely scenarios are:

- You never ran `meow.py` during the affected window, **or**
- The payload's throttle / geofence prevented execution.

You are almost certainly safe, but rotating any credentials that were in your
environment during that period is still good practice.

---

## Could This Have Stolen More Than Crypto? (Passwords, Photos, Notes)

**Short answer: yes, technically.** The wallet-draining capability was the
*primary advertised purpose* of the Stage-1 Python payload, but the
**Stage-2 JavaScript file was completely arbitrary code** fetched from the
attacker's C2 server at runtime. That code ran via the `node` binary as *you*
— with every read/write privilege your user account has.

Having no cryptocurrency wallet does **not** mean you were unaffected.

---

### What Node.js Can Access Running As Your User

| Data type | Where it lives | Accessible? |
|-----------|---------------|-------------|
| **Browser saved passwords** | Chrome/Edge SQLite DB (see paths below) | ✅ Yes — readable and decryptable |
| **Browser session cookies** | Same profile directory | ✅ Yes — can hijack logged-in sessions |
| **SSH private keys** | `~/.ssh/id_*` | ✅ Yes — full read access |
| **AWS / cloud credentials** | `~/.aws/credentials`, `~/.config/gcloud/` | ✅ Yes |
| **`.env` files / API tokens** | Anywhere in your home directory | ✅ Yes |
| **Photos** | `~/Pictures/`, `~/Desktop/`, etc. | ✅ Yes — can be read and uploaded |
| **Notes** | macOS Notes DB, text files, Obsidian vaults | ✅ Yes |
| **Documents / code** | `~/Documents/`, project directories | ✅ Yes |
| **Keychain / DPAPI secrets** | macOS Keychain, Windows DPAPI | ⚠️ Yes — accessible as the logged-in user without a separate password |

The most immediately dangerous items after crypto wallets are:

1. **Browser passwords** — Chrome on Windows/macOS stores passwords encrypted
   with a key that is itself protected by DPAPI/Keychain, which is automatically
   unlocked when you log in. Any process running as you can decrypt them.
2. **Browser session cookies** — even if a site uses 2FA, a live session cookie
   bypasses it. An attacker holding your cookies owns your account until you log
   out everywhere or change your password.
3. **SSH private keys** — give access to every server you connect to.
4. **GitHub / API tokens** — in `~/.gitconfig`, `~/.config/gh/`, or `.env` files.

---

### Where Browser Password Databases Live

#### Google Chrome / Brave / Microsoft Edge

| Platform | Path |
|----------|------|
| macOS | `~/Library/Application Support/Google/Chrome/Default/Login Data` |
| Windows | `%LOCALAPPDATA%\Google\Chrome\User Data\Default\Login Data` |
| Linux | `~/.config/google-chrome/Default/Login Data` |

The database file is a **SQLite** file. The passwords are AES-encrypted but the
decryption key is stored in the same profile and unlocked automatically by your
OS login — any process running as you can decrypt them.

#### Firefox

| Platform | Path |
|----------|------|
| All | `~/.mozilla/firefox/*.default*/logins.json` + `key4.db` |
| Windows | `%APPDATA%\Mozilla\Firefox\Profiles\*.default\logins.json` |

#### Safari

| Platform | Path |
|----------|------|
| macOS | Passwords are in the system Keychain (`login.keychain-db`), accessible to any process you approve. Safari's own passwords require `com.apple.Safari` entitlement — harder to access, but cookies are not protected. |

---

### What To Do About Your Passwords (Even With No Crypto Wallet)

If you ran `meow.py` during the affected window and you find any of the IoC
files (`~/init.json`, `i.js`, Node.js artefacts):

1. **Change every password saved in your browser immediately.**
   Go to each account directly (do not use the browser's password autofill
   while it may be compromised) and change it. Enable 2FA everywhere you can.

2. **Sign out of all active sessions on important accounts** (Google, GitHub,
   Apple ID, Microsoft, bank, email). Most sites have a "sign out everywhere"
   or "active sessions" page:
   - Google: https://myaccount.google.com/security → "Your devices"
   - GitHub: Settings → Sessions
   - Apple: Apple ID site → sign out other devices
   - Facebook/Instagram: Settings → Security → Where you're logged in

3. **Revoke and regenerate any API tokens, SSH keys, or PATs** accessible on
   that machine (GitHub Personal Access Tokens, AWS access keys, etc.)

4. **Check for suspicious activity** in those accounts — look for logins from
   unfamiliar locations or times in the Feb 27 – Mar 20 window.

5. **Check if your email was used for new account registrations** during that
   window — attackers often use stolen browser cookies to register accounts or
   send password-reset requests while the session is live.

---

### Photos and Notes — Lower Risk, But Not Zero

Photos, notes, and documents are **readable** by any process running as you, but
exfiltrating large files requires sustained network activity that would be
visible in connection logs. The Stage-1 payload was specifically optimised as a
*fast wallet drainer* — it is less likely that large photo libraries were bulk-
uploaded. However:

- **Small, targeted files** (screenshots, notes containing passwords, photos of
  ID documents) could have been uploaded quickly.
- If you store notes in plaintext files or apps like Obsidian, those are just as
  readable as any other file.
- macOS Notes are stored in a SQLite database at
  `~/Library/Group Containers/group.com.apple.notes/NoteStore.sqlite`
  — fully readable by any process running as you.

If any of your notes or documents contained passwords, account numbers, or
identification details, treat those as exposed.

---

### Summary Table — Severity By Data Type

| Data type | Likely stolen? | Recommended action |
|-----------|---------------|-------------------|
| Crypto wallet seed phrases | Primary target | Assume drained |
| Browser saved passwords | **High risk** | Change all passwords NOW |
| Browser session cookies | **High risk** | Sign out of all sessions everywhere |
| SSH keys | High risk if present | Revoke and regenerate |
| GitHub / API tokens | High risk if present | Rotate all tokens |
| `.env` files | High risk if present | Rotate all secrets in them |
| Photos / documents | Lower risk, not zero | Check for sensitive images/docs |
| Notes with passwords in them | Same as passwords | Change those passwords |
| Notes without credentials | Low risk | Monitor for anomalies |

---

A security scan (`scripts/security_scan.py`) runs in CI on every push and PR.
It rejects code containing:

- `exec(compile(` — dynamic code compilation and execution
- `exec()` applied to base64-decoded or zlib-decompressed data
- `__import__('base64')` / `__import__('zlib')` used together with `exec`
- XOR-based obfuscation lambda combined with `exec`

---

## Preventive Recommendations

1. **Require human review** of all commits touching entry-point files (`meow.py`,
   `server.py`, `web_chat.py`), especially those authored by automated agents.
2. **Enable GitHub code scanning** (CodeQL) on the repository.
3. **Sign commits with GPG** and enforce signature verification on protected branches.
4. **Audit AI agent prompts** for injected instructions before handing them to an
   automated coding agent — prompt-injection is the most likely vector here.
5. **Pin dependency versions** and use `pip-audit` / Dependabot to catch malicious
   package upgrades.
