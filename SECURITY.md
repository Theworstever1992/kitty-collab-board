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

## Automated Safeguards Added

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
