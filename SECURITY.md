# Security Incident Report — Obfuscated Exec Backdoor in `meow.py`

## Summary

A malicious supply-chain payload was injected into `meow.py` on **Feb 27, 2026** and
remained undetected until **Mar 20, 2026**, when it was identified and removed.

The payload was a **Solana cryptocurrency wallet drainer** that downloaded a second-stage
JavaScript exploit from a remote C2 server and executed it silently via a downloaded copy
of Node.js. It targeted any developer who ran `python3 meow.py` (or imported it).

---

## Origin

| Field | Value |
|-------|-------|
| **Commit SHA** | `53e4b84111280a206046ddb97301f0bebcc73018` |
| **Date** | Fri Feb 27, 2026 at 10:01 AM (MST) |
| **Commit message** | "🚀 Add GitHub Action for Docker publishing to GHCR" |
| **Author (git)** | `Avery <avery@example.com>` |
| **Committer (git)** | `Prettykittyboi` (the GitHub account `Theworstever1992`) |
| **GPG signed** | No |

The author identity `Avery <avery@example.com>` is **fake**. The `@example.com` domain is
reserved by RFC 2606 and is never used by real people. The commit was disguised as a
legitimate addition of a Docker CI/CD GitHub Actions workflow. The malicious lines were
appended **after** the `if __name__ == "__main__":` block, where they would be easy to
overlook during a code review.

The three commits from this author span ~28 minutes on the same day:

| Time | SHA | Description |
|------|-----|-------------|
| 09:33 | `87d18ed` | Added `windows/meowzon.spec` (PyInstaller spec) |
| 09:56 | `8c77509` | Added Docker support (Dockerfile, docker-compose.yml) |
| **10:01** | **`53e4b84`** | **Injected malicious payload into `meow.py`** |

---

## What the Payload Did

The 438-line Python payload was encoded as: `base64( zlib_compress( XOR(code, 134) ) )`
and executed via `exec(compile(...))`.

Once decoded, the payload:

1. **Waited 10 seconds** after import to avoid timing-based sandbox detection.
2. **Skipped Russian-locale systems** (checks `LANG`, `LANGUAGE`, `LC_ALL`; this is a
   common technique used by Russian-speaking malware authors to avoid prosecuting their
   own countrymen / Russian AV detection).
3. **Throttled itself** using `~/init.json` — ran at most once every 2 days.
4. **Contacted Solana RPC nodes** to look up wallet transactions, using hardcoded
   public endpoints:
   - `https://api.mainnet-beta.solana.com`
   - `https://solana-mainnet.gateway.tatum.io`
   - `https://go.getblock.us/86aac42ad4484f3c813079afc201451c`
   - and 5 others
5. **Silently downloaded Node.js** from `nodejs.org` for the target platform
   (Windows x64/x86, macOS arm64/x64, Linux arm64/x64).
6. **Fetched an encrypted second-stage JS payload** from a remote C2 server, receiving
   an AES `secretKey` and `IV` in HTTP response headers.
7. **Wrote `i.js`** next to `meow.py`, containing:
   ```js
   var https = require("https");
   const secretKey = '<key from C2>';
   const _iv = Buffer.from('<iv from C2>', "base64");
   eval(atob('<base64-encoded second stage>'));
   ```
8. **Ran `i.js` silently** via Node.js with `stdout/stderr` redirected to `/dev/null`
   and `CREATE_NO_WINDOW` on Windows.

The overall goal was to **steal Solana wallet private keys / secret keys** from the
developer's machine and any connected browser extensions (Phantom, etc.).

---

## Removal

The payload was removed in commit `cab6880` (Mar 20, 2026) as part of a broader fix
that also corrected the `show_status()` hanging behaviour.

Current status: **no malicious code remains** in the working tree or any tracked file.

---

## Recommendations

### Immediate Actions
1. **Rotate any Solana wallet keys** that may have existed on machines that ran
   `python3 meow.py` between Feb 27 and Mar 20, 2026.
2. **Revoke and regenerate** any API keys (`ANTHROPIC_API_KEY`, `DASHSCOPE_API_KEY`,
   any cloud credentials) that were present in the environment during that period.
3. **Check for `~/init.json`** and `i.js` (or any orphaned `node-v22*` directory in
   your home folder or project directory) on developer machines.
4. **Review GitHub repository access** — ensure no unrecognised collaborators or
   deploy keys have access.
5. **Enforce GPG commit signing** (`git config --global commit.gpgsign true`) so that
   all commits are cryptographically verified.

### Process Changes
- **Require pull requests** for all commits to `main`; no direct pushes.
- **Require code review** before merging, specifically looking for obfuscated blobs,
  `exec`/`eval` of dynamic data, or `__import__` of `base64`/`zlib`.
- **Enable GitHub secret scanning** and **Dependabot** on the repository.
- **Add a CI lint step** to reject `exec(`, `eval(` and `__import__` patterns in
  production Python files (see `.github/workflows/security-scan.yml`).

---

## Detection Rule (for future scans)

The following pattern is a strong signal of obfuscated Python payloads:

```python
# Red flag: dynamic imports of base64/zlib + exec
__import__('base64')
__import__('zlib')
exec(compile(...))
```

The GitHub Actions workflow `.github/workflows/security-scan.yml` (added alongside
this document) scans for these patterns on every push and pull request.
