# WATCH V1 manual release checklist

This checklist covers the remaining work that cannot be honestly completed by hosted CI.

## 1. Intended-workstation scheduler validation

- [ ] Start from the intended Windows workstation.
- [ ] Run `WATCH.ps1 task-plan` and review the generated manifest.
- [ ] Run `WATCH.ps1 task-install` using the approved interval, workspace, evidence directory, and maximum-work value.
- [ ] Run `WATCH.ps1 task-verify` and retain its JSON evidence.
- [ ] Confirm current-user limited privilege, no stored password, and `IgnoreNew` overlap prevention in Task Scheduler.
- [ ] Observe at least one scheduled invocation and retain its result JSON.
- [ ] Validate uninstall and, where a prior task backup exists, rollback behavior.

## 2. Approved live-run example

- [ ] Select one explicitly approved low-risk public target.
- [ ] Run one bounded read-only collection.
- [ ] Review URLs, headers, errors, and metadata for sensitive or identifying content.
- [ ] Sanitize and commit one representative report.

## 3. Interactive clean-checkout review

- [ ] Clone or extract the repository into a clean Windows location.
- [ ] Follow the README without undocumented steps.
- [ ] Confirm setup, verification, demo, workbench launch, planning, one-shot execution, scheduler planning, and review export are understandable.
- [ ] Record any friction as a release-blocking issue before tagging.

## 4. Portfolio presentation review

- [ ] Review README positioning and claims for accuracy.
- [ ] Review CI proof artifacts and workbench screenshots.
- [ ] Select final portfolio screenshots.
- [ ] Confirm repository description, topics, and public-safe sample data.

## 5. Stable release decision

- [ ] Confirm automated readiness is `PASS` with no automated blockers.
- [ ] Confirm every manual item above is complete.
- [ ] Confirm no open release-blocking issue remains.
- [ ] Set the intended stable version.
- [ ] Create the first stable Git tag and release notes.

The project must not claim a completed stable V1 release until all sections are complete.
