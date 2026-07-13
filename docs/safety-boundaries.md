# Safety boundaries

WATCH is read-only first.

## Allowed

- process public-safe sample targets;
- validate structured local input;
- run deterministic analysis;
- store local run and action records;
- produce local reports;
- run future approved public checks at low volume with explicit timeouts.

## Not allowed without explicit design and approval

- modify DNS, domains, websites, or external systems;
- log in to client systems;
- store credentials, tokens, or secrets;
- send email or contact leads;
- submit forms;
- bypass authentication, CAPTCHA, rate limits, or access controls;
- broad scanning or aggressive crawling;
- place private client data in the public repository;
- claim confirmed root cause from incomplete evidence.

## Data rule

Only sanitized sample data belongs in the public repository.
