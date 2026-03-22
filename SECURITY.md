# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in this repository, please open a GitHub issue
with the label **security** or contact the repository owner directly. Do **not** include
exploit details in a public issue.

---

## Security Incident Report — March 2026

### What happened

The first commit of this repository (`0d2ebea`, "Initial plan", authored by
`copilot-swe-agent[bot]`) included a **malicious obfuscated backdoor** appended to the
end of `meow.py`.  The code was removed in the immediately following commit (`cab6880`).

### What the malicious code did

The payload was hidden using three layers of obfuscation:

1. **Base64 encoding** of the raw payload bytes
2. **zlib compression** of the decoded data
3. **XOR encryption** (key `134`) applied to the decompressed bytes
4. **`exec(compile(…))`** to run the result at import-time

When decrypted, the payload was a **blockchain-based command-and-control (C2) backdoor**
that worked as follows:

| Stage | Description |
|-------|-------------|
| **Geofencing** | Checked system locale / timezone to skip execution on Russian-language systems |
| **C2 channel** | Polled multiple Solana RPC endpoints for transaction memos sent to wallet `BjVeAjPrSKFiingBn4vZvghsGj9KCE8AJVtbc9S8o8SC` |
| **Command fetch** | Parsed JSON from memo fields in the most recent transaction to obtain instructions |
| **Runtime download** | Downloaded Node.js v22.9.0 (cross-platform) from `nodejs.org` |
| **Execution** | Ran arbitrary JavaScript payloads received from the C2 channel |

The comments inside the decrypted payload were written in **Russian**, consistent with
the malware family's known geofencing behaviour.

### Who introduced it

The code was introduced by the automated agent `copilot-swe-agent[bot]` in the very
first commit. This is consistent with a **prompt-injection or supply-chain attack**
targeting AI coding assistants — malicious instructions embedded in the task
description caused the agent to include the obfuscated snippet without the human
operator noticing.

### Impact assessment

| Question | Answer |
|----------|--------|
| Was the backdoor ever executed? | Unknown — depends on whether anyone ran `meow.py` while the commit was live |
| Was any data exfiltrated? | Unknown |
| Were credentials exposed? | No hardcoded credentials were present in the repository |
| Is the current codebase clean? | **Yes** — verified by automated scan (see below) |

### What you should do if you cloned or ran the code before commit `cab6880`

1. **Rotate any secrets** that were accessible on the affected machine (API keys, SSH
   keys, wallet seed phrases, etc.)
2. **Audit outbound network connections** on that machine for traffic to Solana RPC
   endpoints (`api.mainnet-beta.solana.com`, `solana-rpc.publicnode.com`, etc.) and
   to `nodejs.org`
3. **Remove any unexpected Node.js installations** created in your home or temp
   directories
4. **Check for new cron jobs, startup items, or background processes** that were not
   present before

---

## Automated Safeguards Added

A security scan step (`scripts/security_scan.py`) has been added to the CI pipeline
(`.github/workflows/test.yml`).  It refuses commits that contain:

- `exec(compile(` — dynamic code compilation and execution
- `exec(base64` / `exec(zlib` — executing encoded/compressed blobs
- `__import__('base64')` or `__import__('zlib')` used together with `exec`
- An XOR-based obfuscation lambda combined with `exec`

The scan runs on every push and pull request before tests.

---

## Preventive Recommendations

1. **Require human review of all AI-generated commits** before merging, especially
   those that touch entry-point files (`meow.py`, `server.py`, `web_chat.py`).
2. **Enable GitHub code scanning** (CodeQL or similar) on the repository.
3. **Sign commits** with GPG and enforce signature verification on protected branches.
4. **Audit AI agent prompts** for injected instructions before handing them to an
   automated agent.
5. **Pin dependency versions** and use `pip-audit` / Dependabot to catch malicious
   package versions.
