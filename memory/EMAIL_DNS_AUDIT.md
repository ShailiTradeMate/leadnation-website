# Vametra email / DNS / Resend / Google Workspace audit — 2026-06 (READ-ONLY, no changes made)

Evidence: live DNS (8.8.8.8 + 1.1.1.1), user-supplied zone export (2026-10-08 22:23 UTC),
code inspection of /app/backend/emailer.py + all callers, /app/backend/.env (keys masked),
frontend/src/lib/AuthContext.jsx + firebase.js.

## 1. Executive summary
- Nothing is broken. Google Workspace and Resend already coexist correctly on vametra.com.
- Google's "SPF = CAUTION" is COSMETIC: Google compares the literal TXT string at vametra.com
  against its recommended `v=spf1 include:_spf.google.com ~all`. Ours is GoDaddy's managed
  indirect include (`dc-aa8e722993._spfm`), which resolves to _spf.google.com. Google IS
  authorized. No deliverability impact. 2 of 10 SPF lookups used.
- send.vametra.com (MX feedback-smtp.ap-northeast-1.amazonses.com + SPF include:amazonses.com)
  is Resend's own domain setup (Resend runs on AWS SES, region ap-northeast-1 / Tokyo). It is the
  Return-Path / bounce domain. ACTIVE. Deleting it breaks Resend SPF + bounce handling.
- Both DKIM keys are valid and non-colliding: google._domainkey (Workspace) and
  resend._domainkey (Resend). Keep both.
- DMARC p=quarantine is SAFE: Google mail passes SPF+DKIM aligned; Resend mail passes DKIM
  aligned (d=vametra.com) and SPF aligned via relaxed alignment on send.vametra.com.
- Three REAL gaps found, none DNS-breaking:
  G1 Resend's `send` SPF is wrapped by GoDaddy's merge wrapper instead of the literal value
     Resend asks for — functionally fine, but Resend's verifier may mark SPF unverified. VERIFY.
  G2 All 36 automated templates send From a human mailbox, admin@vametra.com, with no Reply-To
     and no List-Unsubscribe on digest/weekly mail.
  G3 Email verification + password reset do NOT go through Resend at all — Firebase Auth
     (project trademate-new) sends them from noreply@trademate-new.firebaseapp.com.
  G4 leadnation.app has NO Google DKIM (NXDOMAIN) and a redundant include:resend.dev.

## 2. Current architecture
Inbound  vametra.com / leadnation.app  -> Google Workspace (aspmx.l.google.com set)
Outbound human mail                    -> Google Workspace, From @vametra.com,
                                          SPF via root include -> _spf.google.com,
                                          DKIM s=google d=vametra.com
Outbound app mail                      -> FastAPI emailer.py -> Resend API (SES, ap-northeast-1),
                                          From admin@vametra.com,
                                          MAIL FROM/Return-Path @send.vametra.com,
                                          DKIM s=resend d=vametra.com
Auth mail (verify/reset)               -> Firebase Auth, From noreply@trademate-new.firebaseapp.com
                                          (OUTSIDE vametra.com; DMARC for vametra.com not involved)

## 3. Email-relevant DNS inventory (vametra.com, live-verified)
| Record | Value | Owner |
|---|---|---|
| MX @ | 1 aspmx, 5 alt1, 5 alt2, 10 alt3, 10 alt4 .l.google.com | Google Workspace |
| MX send | 10 feedback-smtp.ap-northeast-1.amazonses.com | Resend (SES bounce/feedback) |
| TXT @ | v=spf1 include:dc-aa8e722993._spfm.vametra.com ~all | GoDaddy-managed SPF (Google) |
| TXT dc-aa8e722993._spfm | v=spf1 include:_spf.google.com ~all | GoDaddy wrapper -> Google |
| TXT send | v=spf1 include:dc-fd741b8612._spfm.send.vametra.com ~all | GoDaddy wrapper -> SES |
| TXT dc-fd741b8612._spfm.send | v=spf1 include:amazonses.com ~all | Resend/SES |
| TXT google._domainkey | v=DKIM1; k=rsa; p=MIIBIjAN… (2048-bit) | Google Workspace |
| TXT resend._domainkey | p=MIGfMA0G… (1024-bit, no v= tag — valid, v= defaults to DKIM1) | Resend |
| TXT _dmarc | v=DMARC1; p=quarantine; adkim=r; aspf=r; rua=mailto:dmarc_rua@onsecureserver.net; | GoDaddy DMARC monitoring |
| TXT @ | google-site-verification=sMIqGat8… | Google site verify (not email) |
| CNAME 2adb81e4…, www, _domainconnect; A 162.159.142.117 / 172.66.2.113 | website | not email |

External DMARC report authorization CONFIRMED:
`vametra.com._report._dmarc.onsecureserver.net TXT "v=DMARC1"` -> rua is authorized and will receive reports.

## 4. Complete SPF resolution tree
ROOT (MAIL FROM @vametra.com)
```
vametra.com TXT "v=spf1 include:dc-aa8e722993._spfm.vametra.com ~all"
 └─(lookup 1) dc-aa8e722993._spfm.vametra.com "v=spf1 include:_spf.google.com ~all"
     └─(lookup 2) _spf.google.com "v=spf1 ip4:74.125.0.0/16 ip4:209.85.128.0/17
        ip6:2001:4860:4864::/56 ip6:2404:6800:4864::/56 ip6:2607:f8b0:4864::/56
        ip6:2800:3f0:4864::/56 ip6:2a00:1450:4864::/56 ip6:2c0f:fb50:4864::/56 ~all"
EFFECTIVE: Google Workspace IPs = PASS. Everything else = SOFTFAIL (~all).
DNS lookups used: 2 / 10. Single SPF TXT at root (no duplicates). Syntax valid.
```
SUBDOMAIN (MAIL FROM @send.vametra.com — what Resend/SES uses)
```
send.vametra.com TXT "v=spf1 include:dc-fd741b8612._spfm.send.vametra.com ~all"
 └─(lookup 1) dc-fd741b8612._spfm.send.vametra.com "v=spf1 include:amazonses.com ~all"
     └─(lookup 2) amazonses.com "v=spf1 ip4:199.255.192.0/22 … ip4:98.77.0.0/16 -all"
EFFECTIVE: Amazon SES IPs = PASS for @send.vametra.com. Lookups 2 / 10. Valid.
```
Answers: Google authorized ✔ · Resend authorized ✔ (via send.vametra.com, NOT root) ·
SES authorized only under send.vametra.com ✔ · SES config IS Resend's ✔ ·
Resend custom Return-Path = send.vametra.com (DNS pattern proves intent; confirm in dashboard) ·
Intentional ✔ · Redundant: only the two GoDaddy wrapper hops · Missing: nothing required ·
No duplicate SPF · No nesting errors · No lookup-limit problem · Root SPF standards-valid.

DO NOT add `include:amazonses.com` to the ROOT SPF: that would authorize every Amazon SES
customer worldwide to send as @vametra.com. The subdomain design is the correct, safer design.

## 5. Exact reason Google shows SPF = CAUTION
Google Admin > Domains > Email setup status does a literal string comparison, not a recursive
SPF evaluation. Recommended `v=spf1 include:_spf.google.com ~all` vs current
`v=spf1 include:dc-aa8e722993._spfm.vametra.com ~all` -> mismatch -> "Caution".
It is advisory only. There is no real SPF problem: Google's netblocks resolve through the chain
(traced above) and Workspace mail passes SPF today.

## 6. DKIM analysis
| Selector | Service | Key | Status |
|---|---|---|---|
| google._domainkey.vametra.com | Google Workspace | RSA 2048, v=DKIM1 present | VALID, Admin = Complete. Do not touch. |
| resend._domainkey.vametra.com | Resend | RSA 1024, p= only (v= optional per RFC 6376) | VALID, resolves. Do not touch. |
No selector collision (different selectors). Both coexist by design — the signing service picks
its own selector. Neither is obsolete. leadnation.app: resend._domainkey present;
google._domainkey.leadnation.app = NXDOMAIN (gap G4).

## 7. DMARC analysis
`v=DMARC1; p=quarantine; adkim=r; aspf=r; rua=mailto:dmarc_rua@onsecureserver.net;`
- Syntactically valid. rua external authorization confirmed (section 3).
- No pct (= 100), no sp (subdomains inherit quarantine), no ruf (no forensic reports).
- Google path: SPF pass + aligned (vametra.com), DKIM pass + aligned -> DMARC PASS.
- Resend path: DKIM d=vametra.com aligned -> PASS; SPF on send.vametra.com is aligned under
  aspf=r (same organizational domain) -> PASS. Either alone satisfies DMARC.
- A failing automated mail would be quarantined (spam folder), not rejected. Risk today is low
  because both paths are authenticated. p=none is NOT necessary; p=quarantine is appropriate,
  and p=reject is a later step once DMARC reports are reviewed for a few weeks.

## 8. Application email flow (code-verified)
Provider for all rows below except the Firebase rows: Resend. From: `Vametra AI <admin@vametra.com>`
(SENDER_EMAIL in backend/.env). Reply-To: NOT SET anywhere in emailer.py. DKIM s=resend d=vametra.com.
SPF domain / Return-Path: send.vametra.com. DMARC: pass (DKIM aligned).
| Email type | Trigger | Backend | Notes |
|---|---|---|---|
| Email verification | signup | FIREBASE (frontend AuthContext.jsx:153 sendEmailVerification) | From noreply@trademate-new.firebaseapp.com — not Resend, not vametra.com |
| Password reset | user request | FIREBASE (AuthContext.jsx:183 sendPasswordResetEmail) | same as above |
| account_created / welcome | post-signup | emailer.send | Resend |
| security_alert, profile_changed, document_updated, account_removed | brain/profile_brain.announce | emailer.send | Resend, Brain-owned comms |
| verify_submitted / approved / rejected / correction | verify.py:607 + admin | emailer.send | Resend |
| verified_weekly (digest) | verify.py:667 APScheduler Mon 08:00 UTC | emailer.send | Resend — bulk, no List-Unsubscribe |
| subscription_granted / revoked / success, payment_success / failed, renewal_reminder | monetize.py | emailer.send | Resend |
| report_generated / report_pdf / shared_report / weekly_report | monetize.py:434, reports | emailer.send | Resend |
| buyers_added / buyer_changed | vbie_admin.py:589, vbie_engine.py:200 | emailer.send | Resend |
| event submitted / under_review / approved / published / rejected / expiring / expired | event_listings.py | send_event_email | Resend |
| subadmin_allocation, admin_pending_digest, admin_signoff_request, signoff_declined, admin_delete_request | subadmin.py, admin_ops.py | emailer.send / notify_admin | Resend, to ADMIN_EMAIL=admin@vametra.com |
| admin_new_lead / admin_new_submission / admin_service_request | leads.py, services.py, event_listings.py | notify_admin | Resend -> Google Workspace inbox |
Failure mode is safe: emailer.send never raises; without RESEND_API_KEY it logs and no-ops.

## 9. leadnation.app (legacy/secondary)
MX = Google ✔ (mailboxes keep working). resend._domainkey present ✔. send.leadnation.app +
dc-fd741b8612._spfm.send.leadnation.app = same Resend/SES pattern ✔. _dmarc identical to vametra.com ✔.
Root SPF: `v=spf1 include:dc-aa8e722993._spfm.leadnation.app include:resend.dev ~all`
 - dc-… -> include:_spf.google.com ✔
 - include:resend.dev -> `v=spf1 include:_spf.google.com -all` = redundant, adds 2 lookups, authorizes nothing extra for your SES sending.
GAP: google._domainkey.leadnation.app = NXDOMAIN -> Workspace mail from @leadnation.app has no DKIM.
Under p=quarantine, forwarded/relayed mail (which breaks SPF) can land in spam.

## 10. Conflict matrix
| Record / config | Service | Purpose | Status | Conflict | Risk | Recommended action |
|---|---|---|---|---|---|---|
| MX @ (Google 5x) | Workspace | inbound mail | GREEN | no | — | keep |
| MX send -> feedback-smtp.ap-northeast-1.amazonses.com | Resend/SES | bounce + feedback loop | GREEN | no | removing breaks Resend bounces | keep |
| TXT @ SPF (via _spfm) | GoDaddy/Google | authorize Workspace | GREEN (works) / YELLOW (Google widget) | no | none functional | optional: replace with literal `v=spf1 include:_spf.google.com ~all` |
| TXT dc-aa8e722993._spfm | GoDaddy | wrapper -> Google | GREEN | no | extra lookup only | keep (or remove with the line above) |
| TXT send SPF (via _spfm.send) | GoDaddy wrapper -> SES | authorize Resend Return-Path | YELLOW | no | Resend verifier may not accept the wrapper | VERIFY in Resend; if unverified, set literal `v=spf1 include:amazonses.com ~all` |
| TXT dc-fd741b8612._spfm.send | Resend/SES | SES netblocks | GREEN | no | — | keep |
| google._domainkey | Workspace | DKIM | GREEN | no | — | keep, do not touch |
| resend._domainkey | Resend | DKIM | GREEN | no | — | keep |
| _dmarc p=quarantine | policy | anti-spoof | GREEN | no | low | keep; review reports before p=reject |
| SENDER_EMAIL=admin@vametra.com | app | From for all 36 templates | YELLOW | no | human + bulk reputation mixed, no Reply-To, no List-Unsubscribe | later: no-reply@ or notifications@ + Reply-To support@ |
| Firebase Auth sender (trademate-new.firebaseapp.com) | Firebase | verify + reset mail | GREY/RED (brand) | no DNS conflict | off-brand, lower trust, unmonitored deliverability | decide: custom Firebase sender domain, or move both flows to Resend |
| leadnation.app missing google._domainkey | Workspace | DKIM | RED (gap) | no | spam risk on forwarded mail | generate DKIM for the secondary domain in Google Admin |
| leadnation.app include:resend.dev | legacy | nothing useful | GREY | no | 2 wasted lookups | optional removal |
| TXT google-site-verification, Bing CNAME, A/www | website | verification | GREEN | no | — | keep |

## 11. Why each control exists (business language)
MX = your post box; without it inbound mail bounces. SPF = the list of post offices allowed to
post letters in your name; stops basic spoofing. DKIM = a tamper-proof wax seal that survives
forwarding; the strongest single signal. DMARC = your published instruction to Gmail/Outlook about
what to do with mail that fails both checks, plus the reports that reveal spoofing. Resend domain
authentication = proof that your app's mail is yours, so it signs as vametra.com instead of
resend.dev. Return-Path / bounce domain = where failures are returned, so Resend can suppress dead
addresses — an unmonitored bounce stream is what destroys sender reputation.
None of SPF, DKIM or DMARC GUARANTEES the inbox. They are the entry ticket. Inbox vs spam is
decided mostly by recipient engagement (opens/replies vs deletes), complaint rate (keep under
~0.1%), bounce/invalid rate, consistent From identity and sending volume pattern, content quality
and link reputation, list hygiene, and for bulk mail the presence of one-click unsubscribe.

## 12. Recommended final configuration (FOR APPROVAL — nothing applied)
KEEP (unchanged): all 5 Google MX · MX send -> feedback-smtp.ap-northeast-1.amazonses.com ·
TXT send SPF chain · google._domainkey · resend._domainkey · _dmarc · site-verification records.
OPTIONAL CHANGE 1 (cosmetic, clears Google "Caution"): root TXT ->
`v=spf1 include:_spf.google.com ~all` (one lookup instead of two; authorized senders unchanged —
Google only). Do it in GoDaddy DNS; note GoDaddy's Domain Connect may try to re-manage the
`_spfm` wrapper. Leave the `dc-aa8e722993._spfm` TXT in place for a week as a safety net.
OPTIONAL CHANGE 2 (only if Resend dashboard shows SPF unverified): `send` TXT ->
`v=spf1 include:amazonses.com ~all`.
OPTIONAL CHANGE 3 (leadnation.app): generate Google DKIM for the secondary domain; optionally drop
`include:resend.dev` from its root SPF.
APP-LEVEL (separate, code change, your call): dedicated From (no-reply@ / notifications@) with
Reply-To: support@vametra.com, List-Unsubscribe + List-Unsubscribe-Post on digest/weekly mail, and
a decision on Firebase verification/reset mail (custom sender domain vs moving to Resend).
REMOVE: nothing. No record in this zone is proven obsolete.

## 13. Implementation order, verification, rollback
Order: (0) collect the UNKNOWN evidence below -> (1) leadnation.app Google DKIM -> (2) root SPF
literal -> (3) send SPF literal only if needed -> (4) app-level From/Reply-To/unsubscribe ->
(5) Firebase sender decision -> (6) after 2-4 weeks of clean DMARC reports consider p=reject.
Change one record at a time, 24-48h apart, TTL 3600 so rollback lands within the hour.
Verify after each step: Google Admin email setup status; Resend dashboard domain = Verified;
send a real test to a Gmail and an Outlook address and read the headers — expect
`spf=pass`, `dkim=pass header.d=vametra.com`, `dmarc=pass`; inbound test to admin@vametra.com and
to the @leadnation.app mailbox; `/api/emails/test` style send for one app template; confirm the
weekly digest still delivers. Rollback: re-paste the exact previous TXT value from the zone export
dated 2026-10-08 (kept in this file, section 3) — no other system depends on these strings.

## 14. UNKNOWN — evidence required (do not guess)
U1 Resend dashboard > Domains > vametra.com: verification state of EACH record, region, and
   whether a custom Return-Path/MAIL FROM (send.vametra.com) is enabled. Decides optional change 2.
U2 Raw headers of one delivered Resend email and one Gmail-sent email (Authentication-Results,
   Return-Path, DKIM-Signature d=/s=). Confirms alignment empirically.
U3 Firebase console > Authentication > Templates: sender address, custom domain, custom SMTP.
   Decides the verification/reset plan.
U4 Google Admin > Apps > Gmail > Authenticate email: is DKIM generated for leadnation.app?
U5 Who owns the GoDaddy DMARC monitoring product behind dmarc_rua@onsecureserver.net, and can you
   read those reports? Without report access, p=reject must not be considered.
