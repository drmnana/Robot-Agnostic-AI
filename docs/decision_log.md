# Decision Log

This document records important project decisions so they are not lost in chat history.

## Decisions

### 000 - Project Name Is ORIMUS

Status: Accepted

Decision:
The system name is ORIMUS.

Reason:
ORIMUS gives the project a clear identity while the engineering architecture remains robot-agnostic and modular.

### 001 - Use A Modular Robot-Agnostic Architecture

Status: Accepted

Decision:
The system should be designed as a robot-agnostic autonomy platform with robot-specific adapters.

Reason:
This allows the same mission, AI, perception, safety, and dashboard layers to support different robot platforms.

### 002 - Keep Project Documents In The Repository

Status: Accepted

Decision:
Architecture, roadmap, phase plans, and important decisions should be saved as files inside the project folder.

Reason:
This keeps the project recoverable and prevents important details from existing only in chat memory.

### 003 - Use Phased Development

Status: Accepted

Decision:
The project will be developed in phases, starting with foundation, environment setup, interfaces, simulation, backend, ROS 2 coordination, then hardware integration.

Reason:
This reduces complexity and avoids debugging too many unstable parts at the same time.

### 004 - First Robot Platform Is Unitree Go2X

Status: Accepted

Decision:
The first robot platform target will be the Unitree Go2X.

Reason:
Starting with one specific robot keeps early development focused. Additional robot platforms can be added later through the platform adapter structure.

### 005 - Start With Simulation

Status: Accepted

Decision:
The first development target will be simulation rather than immediate real-hardware control.

Reason:
Simulation allows mission logic, safety rules, interfaces, and dashboard concepts to be tested before risking real robot hardware.

### 006 - Prefer Windows-Friendly Development

Status: Accepted

Decision:
The development workflow should be friendly to Windows because that is the user's preferred environment.

Reason:
A comfortable development environment is important for learning and steady progress. ROS 2 compatibility details may still require WSL2 Ubuntu, Docker, or a hybrid setup.

### 007 - Use Docker-Based Development

Status: Accepted

Decision:
The project should use a Docker-based development environment while keeping Windows as the host operating system.

Reason:
Docker provides a more repeatable and higher-quality environment for ROS 2, simulation tools, dependencies, and future deployment. It may be harder to learn at first, but it should reduce long-term setup problems.

### 008 - Start With ROS 2 Humble

Status: Accepted

Decision:
The first ROS 2 development container will use ROS 2 Humble on Ubuntu 22.04.

Reason:
Humble is stable, widely supported, and a conservative match for Unitree Go2X-oriented ROS 2 development with Cyclone DDS.

### 009 - Move Vertically Before Horizontally

Status: Accepted

Decision:
ORIMUS should first build a complete vertical slice around the Unitree Go2X simulation path before adding adapters for other robot platforms.

Reason:
A full working path from command request to safety validation to mock robot behavior gives the project a testable foundation. Additional platforms can be added later through the adapter pattern.

### 010 - First Mission Is A Simple Demo Sequence

Status: Accepted

Decision:
The first mission manager implementation will run a simple demo mission: stand, walk forward, stop, and sit.

Reason:
This gives ORIMUS a complete testable mission path without introducing navigation, mapping, payloads, or dashboard complexity too early.

### 011 - Build Generic Payload Framework Before Specialized Payloads

Status: Accepted

Decision:
ORIMUS should first implement a generic payload command and result framework with a mock inspection camera before adding specialized payloads such as chemical detectors, vibration sensors, or face recognition cameras.

Reason:
A generic payload flow keeps the architecture modular and prevents the first payload from forcing hardware-specific assumptions into the core system.

### 012 - Use YAML Mission Configuration

Status: Accepted

Decision:
Mission definitions should be loaded from YAML configuration files instead of being hardcoded in the mission manager.

Reason:
YAML mission files make it easier to define patrol, inspection, scan, and payload-triggering missions without editing Python code.

### 013 - Mission Steps Can Target Robot Or Payload

Status: Accepted

Decision:
Mission YAML steps can target either the robot command path or the payload command path.

Reason:
Real ORIMUS missions will combine movement and sensor actions, such as walking to a point and triggering an inspection camera, chemical scan, or vibration reading.

### 014 - Generate JSON Mission Reports

Status: Accepted

Decision:
ORIMUS should generate structured JSON mission reports from ROS 2 mission, robot, payload, perception, and safety events.

Reason:
Reports make the system auditable and prepare the project for backend, dashboard, replay, and operator review features.

### 015 - Add Operator-Style Mission Commands

Status: Accepted

Decision:
The mission manager should accept `start`, `pause`, `resume`, and `cancel` commands through a ROS 2 mission command topic.

Reason:
Operator control is required before connecting the mission system to a backend, dashboard, or AI planner.

### 016 - Start Backend With A Small FastAPI Skeleton

Status: Accepted

Decision:
The first backend should expose a small HTTP API for health checks, mission config discovery, mission config reading, and report reading before adding ROS 2 command integration.

Reason:
A small backend surface is easier to test and gives the future dashboard a stable API foundation.

### 017 - Use A ROS-Aware Mission API Bridge

Status: Accepted

Decision:
Mission command HTTP endpoints should be exposed by a ROS-aware `mission_api_bridge` package that publishes directly to `/mission/command`.

Reason:
This keeps mission control real-time and avoids temporary file-based command passing between the backend and ROS 2.

### 018 - Backend Forwards Mission Commands To ROS Bridge

Status: Accepted

Decision:
The plain FastAPI backend should expose operator-facing mission command endpoints and forward those requests to the ROS-aware `mission_api_bridge`.

Reason:
This gives dashboards and other clients one stable backend API while keeping ROS 2 topic publishing inside the ROS runtime.

### 019 - Expose Live Runtime State Through The Bridge And Backend

Status: Accepted

Decision:
The ROS-aware mission API bridge should cache the latest mission, robot, payload, perception, and safety messages, then expose them through HTTP runtime endpoints. The backend should forward those runtime endpoints for dashboard and client use.

Reason:
The operator interface needs both command flow and feedback flow. Keeping ROS subscriptions inside the ROS runtime avoids forcing the plain backend to become a ROS node.

### 020 - Serve The First Dashboard From The Backend

Status: Accepted

Decision:
The first ORIMUS operator dashboard prototype should live in `dashboard/` and be served by the FastAPI backend at `/dashboard/`.

Reason:
Serving the prototype from the backend avoids a separate frontend toolchain while the operator workflow is still being proven.

### 021 - Support Mission Reset For Repeated Operator Demos

Status: Accepted

Decision:
The mission manager, ROS mission API bridge, backend, and dashboard should support a `reset` mission command.

Reason:
Operators need to rerun demo and test missions from the dashboard without restarting the ROS launch process.

### 022 - Keep Rolling Runtime Event History

Status: Accepted

Decision:
The ROS mission API bridge should keep a bounded rolling event history from mission, perception, and safety events and expose it through `/runtime/events` and `/runtime/state`.

Reason:
Operators need situational awareness over time, not only the latest state snapshot.

### 023 - Show Latest Mission Report In The Dashboard

Status: Accepted

Decision:
The operator dashboard should summarize mission reports exposed by the backend.

Reason:
Operators need an after-action review view that summarizes mission outcome, event counts, payload results, perception events, and safety events.

### 024 - Use SQLite For Mission Audit Trail

Status: Accepted

Decision:
ORIMUS should persist finalized mission reports to SQLite at `/workspace/data/orimus.db`, with queryable tables for missions, mission events, robot commands, safety events, perception events, and payload results.

Reason:
The defense audit trail must support browsing past missions by date, outcome, sector, and evidence category.

### 025 - Hash Finalized Mission Reports

Status: Accepted

Decision:
Each finalized mission report should include and store a SHA-256 content hash.

Reason:
Content hashes provide a foundation for chain-of-custody checks and future tamper-evidence workflows.

### 026 - Add Sector Metadata To Mission Definitions

Status: Accepted

Decision:
Mission YAML files should include a `sector` metadata field.

Reason:
Sector must be recorded at mission definition and mission event time before reports can be reliably filtered by operating area.

### 027 - Support Evidence-Based Audit Report Filters

Status: Accepted

Decision:
The backend and dashboard should filter mission reports by mission metadata, date range, perception event type, safety-event presence, and blocked-command evidence.

Reason:
Defense audit workflows need to answer questions such as which missions detected a person, which missions had safety interventions, and which commands were blocked.

### 028 - Use A Unified Mission Audit Timeline

Status: Accepted

Decision:
Selected mission reports should default to one chronological timeline that combines mission events, robot commands, safety events, perception events, and payload results.

Reason:
Operators first need to understand what happened in order. Separate evidence panels are useful as drilldowns, but they should not force the operator to mentally interleave parallel tables.

### 029 - Link Safety Events To Affected Commands

Status: Accepted

Decision:
Safety events should carry the affected `command_id`, and report views should display safety verdicts inline with robot commands.

Reason:
Blocked, modified, or approved commands must read as one causal story in the audit trail.

### 030 - Prepare Perception Events For Evidence Artifacts

Status: Accepted

Decision:
Perception events should include `evidence_artifact_url` and `evidence_hash`, even when null or empty in the current mock payload.

Reason:
Future camera frames, sensor captures, and other evidence artifacts should plug into the report model without restructuring the dashboard or database.

### 031 - Define JSON Evidence Package Schema v1.0

Status: Accepted

Decision:
ORIMUS evidence exports should use a documented JSON-only Evidence Package Schema v1.0.

Reason:
The schema version in each export must point to a stable contract. Future versions can extend the package without breaking existing review workflows.

### 032 - Add Export-Level Hashes

Status: Accepted

Decision:
Each evidence package should include an `export_hash`, calculated as SHA-256 over the canonical JSON package with `export_hash` excluded from the hashing input.

Reason:
The mission report `content_hash` verifies the finalized report, while `export_hash` verifies the downloaded package has not changed after export.

### 033 - Verify Evidence Packages With Hash And Semantic Checks

Status: Accepted

Decision:
ORIMUS should provide a JSON evidence package verifier with standard exit codes for valid packages, hash mismatches, schema mismatches, and semantic failures.

Reason:
Audit and compliance workflows need machine-readable verification results. Semantic checks catch internally inconsistent packages even when hashes are recomputed.

### 034 - Add Development-Mode Operator Attribution

Status: Accepted

Decision:
Mission commands should carry a development-mode operator identity from dashboard/backend through the ROS command path into mission reports and safety events. Missing or blank values are recorded explicitly as `anonymous`.

Reason:
The audit trail needs to show who issued a command, including which actions were unattributed. This is attribution only, not authentication.

### 035 - Defer Production Authentication

Status: Accepted

Decision:
The current `X-ORIMUS-Operator` value is self-asserted and trust-based. Production deployment requires a real authentication and authorization design such as JWT, mTLS, or SSO.

Reason:
Development-mode attribution helps demos and audit structure, but it is not non-repudiable identity.

### 036 - Add Operator-To-API Mission Command Policy

Status: Accepted

Decision:
Mission command API requests should be checked against a development-mode operator policy before being forwarded to ROS.

Reason:
Operator attribution answers who issued a command. The policy layer adds the first API governance rule: whether that operator ID is allowed to call that mission command endpoint.

### 037 - Keep API Authorization Separate From Robot Safety

Status: Accepted

Decision:
The operator policy layer is application-level API authorization only. It does not replace, augment, or coordinate with the ROS `safety_manager` or hardware safety constraints.

Reason:
API access control and robot execution safety are independent layers. Mixing them would make the system harder to reason about and could create false confidence.

### 038 - Store Backend Audit Events In The Same SQLite Database

Status: Accepted

Decision:
Backend audit events should be stored in `orimus.db` in a separate `backend_audit_events` table.

Reason:
Keeping mission audit and backend audit in one SQLite database simplifies pilot operations. The table boundary keeps the concepts separate and allows a future datastore migration.

### 039 - Log Allowed And Denied Protected API Calls

Status: Accepted

Decision:
Every protected mission command API call should write a backend audit event, whether allowed or denied.

Reason:
Compliance review needs to answer both what was blocked and what authorized operators actually did.

### 040 - Keep Backend Audit Append-Only

Status: Accepted

Decision:
Backend audit events are append-only at the application layer. The public write method is `record_event`; no update or delete API is exposed.

Reason:
Audit logs should preserve event history rather than mutate it.

### 041 - Defer API Audit Export And Verifier Parity

Status: Accepted

Decision:
API Audit should first ship as dashboard list and filter browsing. JSON export and verifier support for backend API audit events are explicitly deferred to a future ticket.

Reason:
Mission History already has filter, drilldown, export, and verifier workflows. Backend API Audit will eventually need similar review parity, but list and filter browsing is the correct scope for the current operator-dashboard step.

### 042 - Keep Artifact Registry Schema Generic

Status: Accepted

Decision:
The evidence artifact registry should use a deliberately generic schema with free-form `source`, free-form `artifact_type`, and opaque `metadata_json`.

Reason:
Artifact type taxonomy and metadata schema are deferred. They will be defined once real perception sources are integrated.

### 043 - Use Deterministic Evidence Bundles

Status: Accepted

Decision:
ORIMUS evidence bundles should be deterministic ZIP files with fixed member ordering, fixed ZIP timestamps, artifact-id-based bundled paths, canonical JSON, and a manifest `bundle_hash`.

Reason:
Audit handoff verification must be reproducible. Original artifact filenames remain metadata only so bundle paths cannot introduce path traversal risk.

### 044 - Add URL-Addressable Mission Replay

Status: Accepted

Decision:
Mission History should include replay frames that are filterable, speed-controlled, and addressable through dashboard URL parameters such as `frame` and `t`.

Reason:
Reviewers need a narrative way to inspect mission history and share exact moments without losing the forensic drilldown links back to commands, safety events, and artifacts.

### 045 - Pin CTO-Deferred Integration Decisions

Status: Accepted

Decision:
Real robot platform integration and real payload integration should be treated as prominent CTO review items. The repository should link directly to those deferred decisions from the README and current architecture snapshot.

Reason:
The simulation-first software spine can continue advancing, but hardware adapter boundaries, real payload schemas, safety limits, and deployment assumptions should be reviewed before they are finalized.

### 046 - Validate Mission YAML Against A Shared Schema

Status: Accepted

Decision:
Mission YAML files should be validated against a shared schema file at `configs/mission_schema.json`, backed by the Pydantic model in `backend/app/mission_schema.py`.

Reason:
The mission contract should be readable by contributors and enforced automatically by tests, not hidden in mission manager parsing code or only checked by manual CLI usage.

### 047 - Add Versioned Scenario Harness

Status: Accepted

Decision:
Simulation scenario checks should be driven by a versioned manifest at `configs/scenarios.yaml` and runnable one scenario at a time or in `--all` mode.

Reason:
The scenario library should be a repeatable pre-flight tool before demos and commits. Versioning the manifest now makes future expectation migrations explicit.

## Pending Decisions

- Real robot platform adapter design.
- Real payload adapter design.
- Hardware emergency stop and manual override model.
- Real artifact metadata taxonomy.
- Real perception model selection.
- Production authentication strategy.
