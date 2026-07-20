# Website Visibility, Trust & Security Assessment

## Product purpose

Extend WATCH's verified, read-only public-target inspection into a customer-facing diagnostic that answers four business questions:

1. Can customers and search engines reach and understand the website?
2. Can AI-assisted search systems discover and cite its public content?
3. Does the public website present credible trust signals?
4. Are there visible security-posture weaknesses that should be remediated?

The product is a diagnostic and lead-generation service. It is not a penetration test, backlink index, ranking guarantee, or proof that a website is secure.

## Target users

- Small and medium businesses with a public website.
- Agencies or consultants needing repeatable pre-sales evidence.
- Existing Webify clients needing recurring monitoring.

## Core workflow

```text
submit public domain
  -> validate target and prevent private-network access
  -> collect bounded public evidence
  -> evaluate deterministic checks
  -> group findings by business dimension
  -> prioritise confirmed findings
  -> generate a branded review report
  -> offer authorised human review or remediation
```

## MVP dimensions

### Website health

- HTTP status and redirect chain.
- TLS validity and expiry.
- Response duration.
- Page title and basic document availability.
- robots.txt and sitemap availability.
- Canonical and viewport presence.
- Basic metadata and heading clarity.

### Search visibility

- Indexability directives.
- robots.txt rules for mainstream search crawlers.
- Canonical consistency.
- Structured-data presence and parseability.
- Public business identity and service clarity signals.

### AI discoverability readiness

The MVP measures technical readiness, not a universal LLM ranking.

- Access rules for OAI-SearchBot, GPTBot, Google-Extended and common search crawlers.
- Important content available in server-returned HTML.
- Organisation/service facts expressed clearly.
- Structured data supporting organisation, local business, service, product, article or person entities.
- Source-worthy content signals such as case studies, original evidence, author information and dated pages.

Sampled LLM prompt testing is deferred to a paid or operator-approved workflow because responses are nondeterministic and API-backed execution creates cost and abuse risks.

### Trust and authority

- Contact and about-page discoverability.
- Privacy and legal-page discoverability.
- Author or organisational identity signals.
- Consistent visible business facts.
- External backlink/citation data only through an optional provider adapter; no provider is required for the MVP.

### Public security posture

- HTTPS enforcement and TLS expiry.
- HSTS.
- Content-Security-Policy.
- X-Content-Type-Options.
- frame-ancestors or X-Frame-Options.
- Referrer-Policy.
- Permissions-Policy.
- Public cookie flags observable in responses.
- Server/framework information disclosure.
- Mixed-content indicators in collected HTML.
- security.txt availability.
- SPF, DMARC and DNSSEC indicators where obtainable through bounded DNS lookups.

## Safety boundaries

The free/public workflow must remain passive or minimally interactive and bounded:

- Public HTTP GET/HEAD and DNS lookups only.
- No form submission.
- No authentication attempts.
- No credential handling.
- No port scanning.
- No brute force or content discovery wordlists.
- No exploit payloads.
- No broad crawling.
- No automated vulnerability claims.
- No access to loopback, link-local, private, reserved or non-public targets.
- Strict redirect revalidation on every hop.
- Per-target request, byte, redirect and time limits.

Any active vulnerability assessment requires verified ownership or written authorisation and a separately defined scope.

## Report language

Reports must distinguish confirmed observations, inferred risks, unavailable evidence and manual-review requirements.

Never state that a website is secure or that no vulnerabilities exist. Preferred wording:

> No critical issue was detected within the limited public checks performed. This assessment is not a penetration test and does not inspect authenticated functionality, source code, server configuration or private infrastructure.

## First useful vertical slice

```text
public URL
  -> existing WATCH target validation and HTTP/TLS collection
  -> robots and homepage metadata collection
  -> deterministic AI-crawler and security-header checks
  -> JSON assessment model
  -> HTML report section
  -> unit, integration and browser proof
```

## Non-goals for the first slice

- Live querying of multiple LLMs.
- A proprietary backlink index.
- Automatic outreach or link purchasing.
- CMS login or remediation.
- Active DAST or penetration testing.
- Multi-tenant billing and accounts.
- Claims about rankings, citations or security guarantees.

## Commercial path

1. Free automatic snapshot with a small number of evidence-backed findings.
2. Paid human-reviewed assessment with competitor and sampled AI-presence analysis.
3. Quoted remediation work.
4. Recurring monitoring for availability, certificates, visibility controls and public security posture.
