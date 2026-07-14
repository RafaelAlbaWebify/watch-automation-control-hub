# Safety boundaries

WATCH is read-only first.

## Allowed

- process public-safe sample targets;
- validate structured local input;
- run deterministic analysis;
- store local target, schedule, occurrence, retry-attempt, run, action, and report records;
- perform explicit single-occurrence execution against approved public targets;
- inspect bounded missed and stale occurrence attention without changing state;
- retry a terminal failed occurrence only through an explicit operator request with a recorded reason;
- produce local reports;
- run future approved public checks at low volume with explicit timeouts.

## Retry boundary

- the original occurrence remains unchanged;
- only terminal `failed` occurrences are eligible;
- claimed, executing, completed, partial, and missed occurrences are rejected;
- stale executing work is visibility-only because the original process may still be active;
- the linked schedule and target must still exist and be enabled;
- each retry is stored as a separate attempt before collection begins;
- each attempt preserves its own completed, partial, or failed result and optional run link;
- a non-blank operator reason is mandatory;
- no more than three attempts are allowed per occurrence;
- no timer, automatic retry loop, batch retry, or background retry process is permitted.

## Not allowed without explicit design and approval

- modify DNS, domains, websites, or external systems;
- log in to client systems;
- store credentials, tokens, or secrets;
- send email or contact leads;
- submit forms;
- bypass authentication, CAPTCHA, rate limits, or access controls;
- broad scanning or aggressive crawling;
- place private client data in the public repository;
- claim confirmed root cause from incomplete evidence;
- install or modify Windows Task Scheduler tasks;
- automatically retry failed or interrupted work.

## Data rule

Only sanitized sample data belongs in the public repository.
