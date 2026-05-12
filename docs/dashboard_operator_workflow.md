# Dashboard Operator Workflow

The ORIMUS dashboard is organized into URL-addressable tabs so operators can share links and return to the same working context.

## Tabs

- `?tab=ops`: Mission Ops
- `?tab=history`: Mission History
- `?tab=audit`: API Audit
- `?tab=readiness`: System Readiness

The header readiness, backend, ROS bridge, and last-updated indicators remain visible across every tab.

## Surface Map

This map records the pre-reorganization dashboard surface and where each item now lives.

| Existing surface | Post-reorg location | Reachability |
| --- | --- | --- |
| Mission list | Mission Ops | default tab |
| Dashboard refresh | Mission Ops | default tab |
| Operator ID | Mission Ops | default tab |
| Start / pause / resume / cancel / reset | Mission Ops | default tab |
| Runtime mission state | Mission Ops | default tab |
| Robot status | Mission Ops | default tab |
| Payload status | Mission Ops | default tab |
| Live perception/safety event summary | Mission Ops | default tab |
| Live event history | Mission Ops | default tab |
| Mission report filters | Mission History | one tab click or `?tab=history` |
| Mission report list | Mission History | one tab click or `?tab=history` |
| Report integrity hash | Mission History | one tab click or `?tab=history` |
| Copy report hash | Mission History | one tab click or `?tab=history` |
| Export JSON | Mission History | one tab click or `?tab=history` |
| Export Bundle | Mission History | one tab click or `?tab=history` |
| Export PDF | Mission History | one tab click or `?tab=history` |
| Mission Replay | Mission History | one tab click or `?tab=history` |
| Audit Timeline | Mission History | one tab click or `?tab=history` |
| Commands / Safety / Perception / Payload detail panels | Mission History | one tab click or `?tab=history` |
| API Audit filters | API Audit | one tab click or `?tab=audit` |
| API Audit event list | API Audit | one tab click or `?tab=audit` |
| API Audit JSON export | API Audit | one tab click or `?tab=audit` |
| Readiness detail panel | System Readiness | one tab click or `?tab=readiness` |
| Manual readiness refresh | System Readiness | one tab click or `?tab=readiness` |

No existing action was removed. Mission operations remain on the default tab, while review and system diagnostics moved into named tabs.

## URL State

The dashboard reads `tab` from the URL on load and updates it when the operator changes tabs.

Replay URL state still works inside Mission History:

```text
/dashboard/?tab=history&frame=3
/dashboard/?tab=history&t=1778483505
```
