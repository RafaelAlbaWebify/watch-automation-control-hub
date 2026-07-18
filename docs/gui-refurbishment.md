# WATCH GUI refurbishment foundation

## Objective

Bring WATCH into the same professional operations-suite family as TRACE without changing
WATCH's completed scheduling, collection, retry, evidence, reporting, or release behaviour.

The interface should communicate a local-first operational control surface rather than a
generic dashboard or consumer web application.

## Reference hierarchy

1. **TRACE** is the primary portfolio-suite reference for shell, typography, spacing,
   navigation, tables, status treatment, responsive behaviour, and proof discipline.
2. The supplied **Production Suite** screens guide industrial information hierarchy,
   compact metrics, table-first workflows, and restrained operational colour.
3. The supplied **Dashforge** screens guide dashboard composition only. Their sales-oriented
   density and decorative widget volume are not part of the WATCH target state.

## Shared suite language

- Fixed dark navy application sidebar on desktop.
- Light operational canvas with a compact top bar.
- Clear page title, one-sentence operational description, and restrained actions.
- White panels with thin slate borders, subtle shadows, and moderate radii.
- Compact uppercase metric labels and prominent values.
- Table-first evidence views with horizontal overflow containment.
- Semantic status treatment:
  - green: successful, enabled, resolved, healthy;
  - amber: partial, claimed, executing, missed, stale, acknowledged;
  - red: failed, critical, open, disabled;
  - slate: neutral or unknown.
- Strong keyboard focus and a persistent skip link.
- Mobile navigation becomes a horizontally scrollable application bar rather than an
  off-canvas interaction that could hide operator routes.

## WATCH-specific identity

WATCH retains its own purpose and terminology:

- **WATCH** as the concise product name;
- **Web Operations Control Hub** as the product descriptor;
- local operator mode and evidence retention visible in the shell;
- targets, schedules, occurrences, attempts, runs, changes, and actions remain explicit;
- no visual implication of external remediation or autonomous control.

## Safety boundary

This phase is presentation-only. It must not change:

- target, schedule, occurrence, attempt, run, action, or report models;
- API routes or response contracts;
- due-time and idempotent-claim behaviour;
- retry limits or evidence immutability;
- collector behaviour;
- Task Scheduler integration;
- release packaging or verification.

## Delivery sequence

1. Shared application shell and token foundation.
2. Dashboard information hierarchy and operator summaries.
3. Table and detail-page consistency.
4. Narrow viewport and keyboard/browser proof.
5. Updated portfolio screenshots and repository presentation.

Each slice must preserve the existing operator tests and pass the complete Linux, Windows,
clean-checkout, visual, and release-readiness gates before merge.
