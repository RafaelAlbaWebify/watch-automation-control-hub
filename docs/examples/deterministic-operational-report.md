# WATCH Operational Report

> Sanitized deterministic example. This file demonstrates the report contract without claiming a live network capture.

- Run ID: `run-example-0001`
- Target: `public-demo`
- Status: **completed**
- Started: 2026-07-14T10:00:00+00:00
- Finished: 2026-07-14T10:00:01+00:00
- Previous run: `none`

## Observations

| Field | Value |
|---|---|
| http_status | 200 |
| final_url | https://example.com/ |
| redirect_count | 0 |
| redirect_chain | [] |
| response_ms | 180 |
| tls_days_remaining | 90 |
| page_title | Evidence Demo |
| content_type | text/html; charset=utf-8 |
| content_length_bytes | 54 |
| response_headers | {'cache-control': 'public, max-age=60', 'content-language': 'en', 'etag': '"demo-v1"', 'last-modified': 'Tue, 14 Jul 2026 09:00:00 GMT', 'server': 'example-edge'} |
| resolved_ips | ['203.0.113.10'] |
| errors | [] |

## Changes

- No previous-run change detected.

## Findings

No threshold finding was generated for this deterministic healthy observation.

## Operational actions

- No open operational action was required.

## Limitations

- Values are sanitized deterministic sample data, not a live network capture.
- The response-header set is allowlisted; arbitrary headers are not persisted.
- Findings are deterministic threshold results, not confirmed root causes.
- External systems were not modified.
