# Safety boundaries

WATCH is read-only first.

## Allowed

- process public-safe sample targets;
- validate structured local input;
- run deterministic analysis;
- store local target, schedule, occurrence, attempt, run, action, and report records;
- perform explicit single-occurrence execution against approved public targets;
- inspect bounded missed and stale occurrence attention without changing state;
- retry a terminal failed occurrence only through an explicit operator request with a recorded reason;
- plan the latest due boundary for each schedule without creating claims or executing work;
- execute a bounded set of latest-due items through one explicit foreground invocation;
- install one approved current-user Windows scheduled task that invokes the bounded one-shot runner and exits;
- produce local reports and scheduler proof manifests;
- run approved public checks at low volume with explicit timeouts.

## Retry boundary

- the original occurrence remains unchanged;
- only terminal `failed` occurrences are eligible;
- claimed, executing, completed, partial, and missed occurrences are rejected;
- stale executing work is visibility-only because the original process may still be active;
- the linked schedule and target must still exist and be enabled;
- each retry is stored as a separate attempt before collection begins;
- each attempt preserves its own completed, partial, or failed result and optional run link;
- a non-blank operator reason is mandatory and retained with the attempt;
- no more than three retry attempts are allowed per occurrence;
- no timer, automatic retry loop, batch retry, or background retry process is permitted.

## Due-work planning boundary

- the caller supplies an explicit timezone-aware evaluation timestamp;
- the planner normalizes that timestamp to UTC;
- at most one latest due boundary is considered per schedule;
- the planner reuses the same deterministic occurrence-key calculation as claim evaluation;
- existing occurrence state may be read but is never modified;
- planning creates no claim, execution marker, retry attempt, run, action, or report;
- planning invokes no collector;
- planning performs no catch-up scan, batch execution, automatic retry, or background work.

## One-shot runner boundary

- the caller supplies an explicit timezone-aware evaluation timestamp and a maximum-work limit from 1 to 10;
- the runner reuses the read-only planner and selects only `ready-to-claim` items;
- schedules are processed in deterministic order;
- each selected item is claimed through the existing atomic occurrence service;
- each claimed item is executed through the existing permanent at-most-once execution boundary;
- completed, partial, and failed results are reported separately with optional run linkage;
- repeated invocation at the same boundary does not recollect finished work;
- the command runs once in the foreground and then exits;
- no catch-up scan, retry, concurrency, timer, loop, or background service is permitted.

## Windows Task Scheduler boundary

- one task invokes one foreground one-shot runner and exits;
- the task runs as the current interactive user with limited privilege;
- WATCH stores no password, token, or scheduler credential;
- the interval is explicitly bounded from 5 to 1,440 minutes;
- scheduled `MaxWork` remains explicitly bounded from 1 to 10;
- the runtime adapter generates the current evaluation timestamp in UTC;
- overlapping task instances are blocked with `IgnoreNew`;
- the task execution limit is 30 minutes;
- an existing same-named task is exported to XML before replacement;
- install state and backup location are retained locally;
- uninstall preserves WATCH operational data and scheduler backup evidence;
- rollback restores a previous task only when a valid backup exists;
- CI proves the dry-run manifest but leaves no persistent scheduled task behind;
- actual install, verify, uninstall, and rollback are explicit workstation operator actions.

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
- install a SYSTEM, elevated, password-backed, or hidden scheduled task;
- create one scheduled task per target;
- automatically retry failed or interrupted work.

## Data rule

Only sanitized sample data belongs in the public repository.
