# Collaboration authority

PO explicitly adopts the Progress Studio collaboration model for STRD. These pinned documents were read for MS-1 and are the governing references (not duplicated feature contracts):

- [Engineer Contract](https://github.com/Suzanoo/progress-studio/blob/9e6c0a7b66ab400fd4bfc51f428042c795d549a5/docs/ENGINEER_CONTRACT.md)
- [Engineer Workflow](https://github.com/Suzanoo/progress-studio/blob/9e6c0a7b66ab400fd4bfc51f428042c795d549a5/docs/ENGINEER_WORKFLOW.md)
- [Coordinator Contract](https://github.com/Suzanoo/progress-studio/blob/9e6c0a7b66ab400fd4bfc51f428042c795d549a5/docs/COORDINATOR_CONTRACT.md)

PO owns product decisions and milestone acceptance. Work independently designs, implements and verifies only the authorized scope and performs no Git operations. Coordinator reviews the handoff and conducts acceptance; Git integration requires separate authorization. Do not import Progress Studio-specific EV/Payment/Excel requirements.

Future runs verify relevant deltas; a remote change does not silently alter this recorded baseline. Separate accepted decisions, repository evidence, engineering recommendations and unresolved decisions. Handoff includes baseline, complete changed files, manifest, setup/test commands, actual results, limitations and remaining gates. Stop at the authorized milestone.
