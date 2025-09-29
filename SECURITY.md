# Security Policy

## Supported Versions

Hear me, contributors and maintainers: only ze most current score shall be defended from discord.  
All other editions? Archived in ze library, never to be patched again.

| Version | Supported          |
| ------- | ------------------ |
| 1.x     | :white_check_mark: |
| 0.x     | :x:                |

Only ze **latest stable major release** (1.x) receives ze vigilance of BunBun’s keen ears und my quill.  
Anything older is marked as obsolete; no security corrections vill be written for zem.

---

## Reporting a Vulnerability

If you perceive a crack in ze harmony — a vulnerability, an opening for mischief — you must not announce it upon ze public stage.  
Instead, you vill whisper directly to ze Kapellmeister und his rabbit.

- **Contact (preferred)**: [security@flyingrobots.dev](mailto:security@flyingrobots.dev)  
- **Alternate**: Repository’s “Report a vulnerability” link (GitHub Security Advisories)  
- **Encryption (optional until key is live)**: We accept plaintext reports today; ve vill announce ze PGP key (ID, fingerprint, und download URL) in SECURITY.md und `.well-known/security.txt` once published.  
- **Contents of your report**:  
  - Concise description of ze flaw  
  - Affected version(s)  
  - Steps to reproduce (as precise as a fugue subject)  
- **Acknowledgement**: Within **72 hours**.  
- **Updates**: At least once per **7 business days** (Mon–Fri, US holidays excluded; UTC).  
- **Resolution**: Should ze vulnerability be judged valid, a patch vill be issued upon ze supported version(s).  
  Credit vill be given unless anonymity is requested.  

Do not, under any circumstance, open a public GitHub issue for ze matter. Such disorder vould unleash cacophony. May BunBun have mercy on your code.

---

## Disclosure Timeline

- **Adagio (Day 0–3):** Vulnerability received, acknowledged within 72 hours.  
- **Andante (Day 3–10):** Initial triage and reproduction attempt.  
- **Allegro (Day 10–30):** Fix prepared, tested, and patched in supported version(s).  
- **Finale (Post-Release):** Reporter credited (or kept anonymous), public disclosure note published.  

Any attempt to leap from *Adagio* straight to *Finale* (i.e., public blast before private fix)  
shall be treated as dissonance — *forbidden modulation*.

---

## The Rule of Strictness

Security is no jest. It is ze bass line upon vich all other melodies rely.  
BunBun may stack his Red Bull cans carelessly to ze heavens, but vulnerabilities must be handled mit precision, formality, und care.  

To report in good faith is to join ze orchestra of order.  
To disclose in public before ze patch? Barbaric. Out of tempo. Nein. Verbotten.

## Safe Harbor
If you make a good-faith effort to comply with this policy, we will not pursue civil or criminal action. Do not access user data, pivot laterally, persist, or degrade availability. Limit testing to your own accounts.

## In Scope / Out of Scope
- In scope: vulnerabilities affecting supported versions and first-party services.  
- Out of scope: social engineering, SPF/DMARC reports, rate-limit/DoS, third-party dependencies unless exploitable in our usage, outdated unsupported versions.

## Severity & SLAs
We use CVSS (v3.1/v4.0 when available) to assign severity. Targets: Critical – 7 days, High – 14 days, Medium – 30 days, Low – best-effort.

## CVE & Advisory
We publish advisories via GitHub Security Advisories and request CVEs. We are not a CNA.
---

*Signed,*  
**P.R. PhiedBach**  
Kapellmeister of Commits; Keeper of BunBun’s Red Bull Pyramid
