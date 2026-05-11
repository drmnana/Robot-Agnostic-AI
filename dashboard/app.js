const state = {
  missions: [],
  selectedMissionId: null,
  selectedReportId: null,
  runtime: null,
  latestReport: null,
  reports: [],
  auditEvents: [],
  replayFrames: [],
  replayIndex: 0,
  replayPlaying: false,
  replayTimer: null,
};

const elements = {
  backendStatus: document.querySelector("#backend-status"),
  bridgeStatus: document.querySelector("#bridge-status"),
  lastUpdated: document.querySelector("#last-updated"),
  missionList: document.querySelector("#mission-list"),
  selectedMissionLabel: document.querySelector("#selected-mission-label"),
  operatorId: document.querySelector("#operator-id"),
  commandMessage: document.querySelector("#command-message"),
  refreshButton: document.querySelector("#refresh-button"),
  reportRefreshButton: document.querySelector("#report-refresh-button"),
  commandButtons: document.querySelectorAll("[data-command]"),
  missionStatePill: document.querySelector("#mission-state-pill"),
  missionState: document.querySelector("#mission-state"),
  missionStep: document.querySelector("#mission-step"),
  missionProgress: document.querySelector("#mission-progress"),
  missionMessage: document.querySelector("#mission-message"),
  progressBar: document.querySelector("#progress-bar"),
  robotConnected: document.querySelector("#robot-connected"),
  robotPlatform: document.querySelector("#robot-platform"),
  robotBattery: document.querySelector("#robot-battery"),
  robotMode: document.querySelector("#robot-mode"),
  robotPose: document.querySelector("#robot-pose"),
  payloadActive: document.querySelector("#payload-active"),
  payloadType: document.querySelector("#payload-type"),
  payloadState: document.querySelector("#payload-state"),
  payloadHealth: document.querySelector("#payload-health"),
  payloadMessage: document.querySelector("#payload-message"),
  perceptionEvent: document.querySelector("#perception-event"),
  safetyEvent: document.querySelector("#safety-event"),
  eventCount: document.querySelector("#event-count"),
  eventHistory: document.querySelector("#event-history"),
  reportStatus: document.querySelector("#report-status"),
  reportList: document.querySelector("#report-list"),
  reportFilterOutcome: document.querySelector("#report-filter-outcome"),
  reportFilterMission: document.querySelector("#report-filter-mission"),
  reportFilterSector: document.querySelector("#report-filter-sector"),
  reportFilterPerception: document.querySelector("#report-filter-perception"),
  reportFilterDateFrom: document.querySelector("#report-filter-date-from"),
  reportFilterDateTo: document.querySelector("#report-filter-date-to"),
  reportFilterSafety: document.querySelector("#report-filter-safety"),
  reportFilterBlocked: document.querySelector("#report-filter-blocked"),
  reportFilterClear: document.querySelector("#report-filter-clear"),
  reportId: document.querySelector("#report-id"),
  reportMission: document.querySelector("#report-mission"),
  reportSector: document.querySelector("#report-sector"),
  reportState: document.querySelector("#report-state"),
  reportMissionEvents: document.querySelector("#report-mission-events"),
  reportPayloadResults: document.querySelector("#report-payload-results"),
  reportPerceptionEvents: document.querySelector("#report-perception-events"),
  reportSafetyEvents: document.querySelector("#report-safety-events"),
  reportHash: document.querySelector("#report-hash"),
  reportFullHash: document.querySelector("#report-full-hash"),
  reportCopyHash: document.querySelector("#report-copy-hash"),
  reportExportJson: document.querySelector("#report-export-json"),
  reportExportBundle: document.querySelector("#report-export-bundle"),
  reportTimelineCount: document.querySelector("#report-timeline-count"),
  reportTimeline: document.querySelector("#report-timeline"),
  reportCommandCount: document.querySelector("#report-command-count"),
  reportCommandList: document.querySelector("#report-command-list"),
  reportSafetyListCount: document.querySelector("#report-safety-list-count"),
  reportSafetyList: document.querySelector("#report-safety-list"),
  reportPerceptionListCount: document.querySelector("#report-perception-list-count"),
  reportPerceptionList: document.querySelector("#report-perception-list"),
  reportPayloadListCount: document.querySelector("#report-payload-list-count"),
  reportPayloadList: document.querySelector("#report-payload-list"),
  replayCount: document.querySelector("#replay-count"),
  replayPlay: document.querySelector("#replay-play"),
  replayPrev: document.querySelector("#replay-prev"),
  replayNext: document.querySelector("#replay-next"),
  replayJump: document.querySelector("#replay-jump"),
  replaySpeed: document.querySelector("#replay-speed"),
  replaySlider: document.querySelector("#replay-slider"),
  replayFrame: document.querySelector("#replay-frame"),
  auditRefreshButton: document.querySelector("#audit-refresh-button"),
  auditStatus: document.querySelector("#audit-status"),
  auditList: document.querySelector("#audit-list"),
  auditFilterOperator: document.querySelector("#audit-filter-operator"),
  auditFilterDecision: document.querySelector("#audit-filter-decision"),
  auditFilterEventType: document.querySelector("#audit-filter-event-type"),
  auditFilterDateFrom: document.querySelector("#audit-filter-date-from"),
  auditFilterDateTo: document.querySelector("#audit-filter-date-to"),
  auditFilterClear: document.querySelector("#audit-filter-clear"),
};

elements.refreshButton.addEventListener("click", () => refreshAll());
elements.reportRefreshButton.addEventListener("click", () => refreshLatestReport());
elements.auditRefreshButton.addEventListener("click", () => refreshAuditEvents());
elements.reportCopyHash.addEventListener("click", () => copyReportHash());
elements.reportExportJson.addEventListener("click", () => exportSelectedReport());
elements.reportExportBundle.addEventListener("click", () => exportSelectedReportBundle());
elements.replayPlay.addEventListener("click", () => toggleReplayPlayback());
elements.replayPrev.addEventListener("click", () => setReplayFrame(state.replayIndex - 1, true));
elements.replayNext.addEventListener("click", () => setReplayFrame(state.replayIndex + 1, true));
elements.replayJump.addEventListener("click", () => setReplayFrame(state.replayIndex + 1, true));
elements.replaySpeed.addEventListener("change", () => restartReplayTimer());
elements.replaySlider.addEventListener("input", () => setReplayFrame(Number(elements.replaySlider.value), true));
elements.reportFilterClear.addEventListener("click", () => clearReportFilters());
elements.auditFilterClear.addEventListener("click", () => clearAuditFilters());
[
  elements.reportFilterOutcome,
  elements.reportFilterDateFrom,
  elements.reportFilterDateTo,
  elements.reportFilterSafety,
  elements.reportFilterBlocked,
].forEach((control) => {
  control.addEventListener("change", () => refreshLatestReport({ resetSelection: true }));
});
[
  elements.auditFilterDecision,
  elements.auditFilterDateFrom,
  elements.auditFilterDateTo,
].forEach((control) => {
  control.addEventListener("change", () => refreshAuditEvents());
});
[elements.reportFilterMission, elements.reportFilterSector, elements.reportFilterPerception].forEach((control) => {
  control.addEventListener("input", debounce(() => refreshLatestReport({ resetSelection: true }), 350));
});
[elements.auditFilterOperator, elements.auditFilterEventType].forEach((control) => {
  control.addEventListener("input", debounce(() => refreshAuditEvents(), 350));
});
elements.commandButtons.forEach((button) => {
  button.addEventListener("click", () => sendMissionCommand(button.dataset.command));
});

refreshAll();
setInterval(refreshRuntime, 2000);

async function refreshAll() {
  await Promise.all([refreshMissions(), refreshRuntime(), refreshLatestReport(), refreshAuditEvents()]);
}

async function refreshMissions() {
  try {
    const data = await fetchJson("/missions");
    state.missions = data.missions ?? [];
    if (!state.selectedMissionId && state.missions.length > 0) {
      state.selectedMissionId = state.missions[0].mission_id;
    }
    setStatus(elements.backendStatus, "Backend", "ok");
    renderMissions();
  } catch (error) {
    setStatus(elements.backendStatus, "Backend", "error");
    elements.missionList.innerHTML = `<div class="message-line">${error.message}</div>`;
  }
}

async function refreshRuntime() {
  try {
    state.runtime = await fetchJson("/runtime/state");
    setStatus(elements.backendStatus, "Backend", "ok");
    const bridgeConnected = state.runtime?.bridge?.connected === true;
    setStatus(elements.bridgeStatus, "ROS Bridge", bridgeConnected ? "ok" : "warn");
    renderRuntime();
  } catch (error) {
    setStatus(elements.backendStatus, "Backend", "ok");
    setStatus(elements.bridgeStatus, "ROS Bridge", "error");
    elements.commandMessage.textContent = error.message;
  } finally {
    elements.lastUpdated.textContent = new Date().toLocaleTimeString();
    syncCommandButtons();
  }
}

async function sendMissionCommand(command) {
  if (!state.selectedMissionId) {
    elements.commandMessage.textContent = "Select a mission first.";
    return;
  }

  setCommandButtonsDisabled(true);
  elements.commandMessage.textContent = `Sending ${command} to ${state.selectedMissionId}...`;

  try {
    const response = await fetchJson(`/missions/${state.selectedMissionId}/${command}`, {
      method: "POST",
      headers: {
        "X-ORIMUS-Operator": operatorId(),
      },
    });
    elements.commandMessage.textContent = `${response.command_type} accepted for ${response.mission_id} by ${response.operator_id ?? operatorId()}`;
    await refreshRuntime();
    if (["cancel", "reset", "start"].includes(response.command_type)) {
      await refreshLatestReport();
    }
    await refreshAuditEvents();
  } catch (error) {
    elements.commandMessage.textContent = error.message;
    await refreshAuditEvents();
  } finally {
    syncCommandButtons();
  }
}

async function refreshLatestReport(options = {}) {
  if (options.resetSelection) {
    state.selectedReportId = null;
  }

  try {
    const data = await fetchJson(buildReportListUrl());
    state.reports = data.reports ?? [];
    if (!state.selectedReportId && state.reports.length > 0) {
      state.selectedReportId = state.reports[0].id;
    }
    renderReportList();
    if (state.selectedReportId) {
      state.latestReport = await fetchJson(`/reports/${state.selectedReportId}`);
      renderLatestReport();
      await refreshReplay();
    } else {
      renderReportUnavailable("No mission reports found");
    }
  } catch (error) {
    state.latestReport = null;
    state.reports = [];
    renderReportUnavailable(error.message);
  }
}

function buildReportListUrl() {
  const params = new URLSearchParams();
  addParam(params, "outcome", elements.reportFilterOutcome.value);
  addParam(params, "mission_id", elements.reportFilterMission.value);
  addParam(params, "sector", elements.reportFilterSector.value);
  addParam(params, "perception_event_type", elements.reportFilterPerception.value);
  addDateParam(params, "date_from", elements.reportFilterDateFrom.value, false);
  addDateParam(params, "date_to", elements.reportFilterDateTo.value, true);
  if (elements.reportFilterSafety.checked) {
    params.set("has_safety_event", "true");
  }
  if (elements.reportFilterBlocked.checked) {
    params.set("command_blocked", "true");
  }

  const query = params.toString();
  return query ? `/reports?${query}` : "/reports";
}

function addParam(params, key, value) {
  const trimmed = String(value ?? "").trim();
  if (trimmed) {
    params.set(key, trimmed);
  }
}

function addDateParam(params, key, value, endOfDay) {
  if (!value) {
    return;
  }

  const suffix = endOfDay ? "T23:59:59" : "T00:00:00";
  const timestamp = Math.floor(new Date(`${value}${suffix}`).getTime() / 1000);
  if (!Number.isNaN(timestamp)) {
    params.set(key, String(timestamp));
  }
}

function clearReportFilters() {
  elements.reportFilterOutcome.value = "";
  elements.reportFilterMission.value = "";
  elements.reportFilterSector.value = "";
  elements.reportFilterPerception.value = "";
  elements.reportFilterDateFrom.value = "";
  elements.reportFilterDateTo.value = "";
  elements.reportFilterSafety.checked = false;
  elements.reportFilterBlocked.checked = false;
  refreshLatestReport({ resetSelection: true });
}

async function refreshAuditEvents() {
  try {
    const data = await fetchJson(buildAuditListUrl());
    state.auditEvents = data.events ?? [];
    renderAuditEvents();
  } catch (error) {
    state.auditEvents = [];
    elements.auditStatus.textContent = error.message;
    elements.auditList.innerHTML = `<div class="message-line">No API audit events available.</div>`;
  }
}

function buildAuditListUrl() {
  const params = new URLSearchParams();
  addParam(params, "operator_id", elements.auditFilterOperator.value);
  addParam(params, "decision", elements.auditFilterDecision.value);
  addParam(params, "event_type", elements.auditFilterEventType.value);
  addDateParam(params, "date_from", elements.auditFilterDateFrom.value, false);
  addDateParam(params, "date_to", elements.auditFilterDateTo.value, true);

  const query = params.toString();
  return query ? `/audit/events?${query}` : "/audit/events";
}

function clearAuditFilters() {
  elements.auditFilterOperator.value = "";
  elements.auditFilterDecision.value = "";
  elements.auditFilterEventType.value = "";
  elements.auditFilterDateFrom.value = "";
  elements.auditFilterDateTo.value = "";
  refreshAuditEvents();
}

function renderMissions() {
  if (state.missions.length === 0) {
    elements.missionList.innerHTML = `<div class="message-line">No missions found.</div>`;
    elements.selectedMissionLabel.textContent = "No mission selected";
    syncCommandButtons();
    return;
  }

  elements.missionList.replaceChildren(
    ...state.missions.map((mission) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "mission-card";
      button.dataset.missionId = mission.mission_id;
      button.classList.toggle("selected", mission.mission_id === state.selectedMissionId);
      button.innerHTML = `
        <strong>${escapeHtml(mission.name ?? mission.mission_id)}</strong>
        <span>${escapeHtml(mission.mission_id)} - ${mission.step_count ?? 0} steps</span>
      `;
      button.addEventListener("click", () => {
        state.selectedMissionId = mission.mission_id;
        renderMissions();
      });
      return button;
    }),
  );

  elements.selectedMissionLabel.textContent = state.selectedMissionId ?? "No mission selected";
  syncCommandButtons();
}

function renderRuntime() {
  const runtime = state.runtime ?? {};
  const mission = runtime.mission;
  const robot = runtime.robot;
  const payload = runtime.payload;
  const perception = runtime.perception;
  const safety = runtime.safety;
  const events = runtime.events ?? [];

  const progress = clamp(Number(mission?.progress ?? 0), 0, 1);
  elements.missionState.textContent = mission?.state ?? "No data";
  elements.missionStep.textContent = mission?.current_step ?? "No data";
  elements.missionProgress.textContent = `${Math.round(progress * 100)}%`;
  elements.missionMessage.textContent = mission?.message ?? "No data";
  elements.progressBar.style.width = `${progress * 100}%`;
  setStatus(elements.missionStatePill, mission?.state ?? "Unknown", missionStateClass(mission?.state));

  elements.robotPlatform.textContent = robot?.platform ?? "No data";
  elements.robotBattery.textContent = formatPercent(robot?.battery_percent);
  elements.robotMode.textContent = robot?.mode ?? "No data";
  elements.robotPose.textContent = formatPose(robot?.pose);
  setStatus(elements.robotConnected, robot?.connected ? "Connected" : "Offline", robot?.connected ? "ok" : "warn");

  elements.payloadType.textContent = payload?.payload_type ?? "No data";
  elements.payloadState.textContent = payload?.state ?? "No data";
  elements.payloadHealth.textContent = formatRatioPercent(payload?.health);
  elements.payloadMessage.textContent = payload?.message ?? "No data";
  setStatus(elements.payloadActive, payload?.active ? "Active" : "Idle", payload?.active ? "ok" : "warn");

  elements.perceptionEvent.textContent = perception
    ? `${perception.event_type} from ${perception.source} (${formatRatioPercent(perception.confidence)})`
    : "No data";
  elements.safetyEvent.textContent = safety
    ? `${safety.severity}: ${safety.message}`
    : "No data";
  renderEventHistory(events);
}

function renderEventHistory(events) {
  const recentEvents = [...events].slice(-12).reverse();
  elements.eventCount.textContent = `${events.length} events`;

  if (recentEvents.length === 0) {
    elements.eventHistory.innerHTML = `<li class="empty-event">No events yet</li>`;
    return;
  }

  elements.eventHistory.replaceChildren(
    ...recentEvents.map((event) => {
      const item = document.createElement("li");
      item.className = `history-item ${event.category ?? "event"}`;
      item.innerHTML = `
        <span class="history-meta">${escapeHtml(event.category ?? "event")} - ${formatStamp(event.stamp)}</span>
        <strong>${escapeHtml(event.event_type ?? event.rule ?? "event")}</strong>
        <span>${escapeHtml(event.message ?? "")}</span>
      `;
      return item;
    }),
  );
}

function renderLatestReport() {
  const report = state.latestReport;
  const mission = report?.mission;
  const missionEvents = report?.mission_events ?? [];
  const payloadResults = report?.payload_results ?? [];
  const perceptionEvents = report?.perception_events ?? [];
  const safetyEvents = report?.safety_events ?? [];

  elements.reportStatus.textContent = "Report loaded";
  elements.reportId.textContent = report?.report_id ?? "No data";
  elements.reportMission.textContent = mission?.name ?? mission?.mission_id ?? "No data";
  elements.reportSector.textContent = reportSector(report);
  elements.reportState.textContent = mission?.state ?? "No data";
  elements.reportMissionEvents.textContent = String(missionEvents.length);
  elements.reportPayloadResults.textContent = String(payloadResults.length);
  elements.reportPerceptionEvents.textContent = String(perceptionEvents.length);
  elements.reportSafetyEvents.textContent = String(safetyEvents.length);
  elements.reportHash.textContent = shortenHash(report?.content_hash);
  elements.reportFullHash.textContent = report?.content_hash ?? "No report hash loaded";
  renderAuditTimeline(report);
  renderEvidencePanels(report);
}

function renderReportUnavailable(message) {
  elements.reportStatus.textContent = message || "Mission report not found";
  elements.reportList.innerHTML = `<div class="message-line">No reports available.</div>`;
  elements.reportId.textContent = "No data";
  elements.reportMission.textContent = "No data";
  elements.reportSector.textContent = "No data";
  elements.reportState.textContent = "No data";
  elements.reportMissionEvents.textContent = "0";
  elements.reportPayloadResults.textContent = "0";
  elements.reportPerceptionEvents.textContent = "0";
  elements.reportSafetyEvents.textContent = "0";
  elements.reportHash.textContent = "No data";
  elements.reportFullHash.textContent = "No report hash loaded";
  elements.reportTimelineCount.textContent = "0 entries";
  elements.reportTimeline.innerHTML = `<li class="empty-event">No report yet</li>`;
  state.replayFrames = [];
  stopReplayPlayback();
  renderReplayUnavailable("No replay loaded");
  renderDetailList(elements.reportCommandList, [], "No commands");
  renderDetailList(elements.reportSafetyList, [], "No safety events");
  renderDetailList(elements.reportPerceptionList, [], "No perception events");
  renderDetailList(elements.reportPayloadList, [], "No payload results");
  elements.reportCommandCount.textContent = "0";
  elements.reportSafetyListCount.textContent = "0";
  elements.reportPerceptionListCount.textContent = "0";
  elements.reportPayloadListCount.textContent = "0";
}

function renderReportList() {
  if (state.reports.length === 0) {
    elements.reportList.innerHTML = `<div class="message-line">No reports available.</div>`;
    return;
  }

  elements.reportStatus.textContent = `${state.reports.length} report records`;
  elements.reportList.replaceChildren(
    ...state.reports.slice(0, 8).map((report) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "report-card";
      button.classList.toggle("selected", report.id === state.selectedReportId);
      button.innerHTML = `
        <strong>${escapeHtml(report.name ?? report.mission_id ?? report.id)}</strong>
        <span>${escapeHtml(report.outcome ?? "unknown")} - ${formatStamp({
          sec: report.ended_at_sec,
        })}</span>
        <span>${escapeHtml(report.sector ?? "unspecified sector")}</span>
        <span>${escapeHtml(shortenHash(report.content_hash))}</span>
      `;
      button.addEventListener("click", async () => {
        state.selectedReportId = report.id;
        renderReportList();
        state.latestReport = await fetchJson(`/reports/${report.id}`);
        renderLatestReport();
        await refreshReplay();
      });
      return button;
    }),
  );
}

async function refreshReplay() {
  stopReplayPlayback();
  if (!state.selectedReportId) {
    renderReplayUnavailable("No replay loaded");
    return;
  }

  try {
    const data = await fetchJson(`/reports/${state.selectedReportId}/replay`);
    state.replayFrames = data.frames ?? [];
    const requestedIndex = replayIndexFromUrl(state.replayFrames);
    renderReplay();
    setReplayFrame(requestedIndex, false);
  } catch (error) {
    state.replayFrames = [];
    renderReplayUnavailable(error.message);
  }
}

function renderReplay() {
  const frameCount = state.replayFrames.length;
  elements.replayCount.textContent = `${frameCount} frames`;
  elements.replaySlider.max = String(Math.max(frameCount - 1, 0));
  elements.replaySlider.disabled = frameCount === 0;
  elements.replayPlay.disabled = frameCount === 0;
  elements.replayPrev.disabled = frameCount === 0;
  elements.replayNext.disabled = frameCount === 0;
  elements.replayJump.disabled = frameCount === 0;

  if (frameCount === 0) {
    renderReplayUnavailable("No replay frames available");
  }
}

function renderReplayUnavailable(message) {
  elements.replayCount.textContent = "0 frames";
  elements.replaySlider.value = "0";
  elements.replaySlider.max = "0";
  elements.replayFrame.className = "replay-frame empty";
  elements.replayFrame.innerHTML = `
    <span class="history-meta">${escapeHtml(message)}</span>
    <strong>No frame selected</strong>
    <span>No replay events are available for this report.</span>
  `;
}

function setReplayFrame(index, updateUrl) {
  if (state.replayFrames.length === 0) {
    renderReplayUnavailable("No replay frames available");
    return;
  }

  state.replayIndex = clamp(Math.round(index), 0, state.replayFrames.length - 1);
  const frame = state.replayFrames[state.replayIndex];
  elements.replaySlider.value = String(state.replayIndex);
  elements.replayFrame.className = `replay-frame ${frame.category}`;
  elements.replayFrame.innerHTML = `
    <span class="history-meta">Frame ${frame.frame_index + 1} / ${state.replayFrames.length} - ${escapeHtml(frame.category)} - ${formatAuditTime(frame.timestamp_sec)}</span>
    <strong>${escapeHtml(frame.title)}</strong>
    <span>${escapeHtml(frame.message)}</span>
    ${frame.operator_id ? `<span class="history-detail">operator ${escapeHtml(frame.operator_id)}</span>` : ""}
    ${frame.command_id ? `<button class="replay-link" type="button" data-link-kind="command" data-link-id="${escapeHtml(frame.command_id)}">command ${escapeHtml(frame.command_id)}</button>` : ""}
    ${frame.artifact_url ? `<a class="artifact-link" href="${escapeHtml(frame.artifact_url)}">artifact ${escapeHtml(frame.artifact_url)}</a>` : ""}
  `;
  elements.replayFrame.querySelectorAll("[data-link-kind]").forEach((link) => {
    link.addEventListener("click", () => highlightLinkedRecord(link.dataset.linkKind, link.dataset.linkId));
  });
  if (updateUrl) {
    updateReplayUrl(state.replayIndex);
  }
}

function toggleReplayPlayback() {
  if (state.replayPlaying) {
    stopReplayPlayback();
  } else {
    state.replayPlaying = true;
    elements.replayPlay.textContent = "Pause";
    restartReplayTimer();
  }
}

function stopReplayPlayback() {
  state.replayPlaying = false;
  elements.replayPlay.textContent = "Play";
  if (state.replayTimer) {
    window.clearInterval(state.replayTimer);
    state.replayTimer = null;
  }
}

function restartReplayTimer() {
  if (state.replayTimer) {
    window.clearInterval(state.replayTimer);
    state.replayTimer = null;
  }
  if (!state.replayPlaying || state.replayFrames.length === 0) {
    return;
  }
  state.replayTimer = window.setInterval(() => {
    if (state.replayIndex >= state.replayFrames.length - 1) {
      stopReplayPlayback();
      return;
    }
    setReplayFrame(state.replayIndex + 1, true);
  }, replayIntervalMs());
}

function replayIntervalMs() {
  const speed = Number(elements.replaySpeed.value || 1);
  return Math.max(1000 / speed, 100);
}

function replayIndexFromUrl(frames) {
  const params = new URLSearchParams(window.location.search);
  const frameParam = params.get("frame");
  if (frameParam !== null) {
    return clamp(Number(frameParam), 0, Math.max(frames.length - 1, 0));
  }
  const timeParam = params.get("t");
  if (timeParam !== null) {
    const target = Number(timeParam);
    const index = frames.findIndex((frame) => frame.timestamp_sec >= target);
    return index >= 0 ? index : Math.max(frames.length - 1, 0);
  }
  return 0;
}

function updateReplayUrl(index) {
  const url = new URL(window.location.href);
  url.searchParams.set("frame", String(index));
  window.history.replaceState({}, "", url);
}

function highlightLinkedRecord(kind, id) {
  const selector = kind === "command" ? "#report-command-list" : "#report-perception-list";
  const container = document.querySelector(selector);
  if (!container) {
    return;
  }
  container.scrollIntoView({ behavior: "smooth", block: "nearest" });
  const target = [...container.querySelectorAll(".history-item")].find((item) => item.textContent.includes(id));
  if (target) {
    target.classList.add("linked-highlight");
    window.setTimeout(() => target.classList.remove("linked-highlight"), 1200);
  }
}

function renderAuditEvents() {
  const events = state.auditEvents;
  elements.auditStatus.textContent = `${events.length} API audit events`;

  if (events.length === 0) {
    elements.auditList.innerHTML = `<div class="empty-event">No API audit events found.</div>`;
    return;
  }

  elements.auditList.replaceChildren(
    ...events.slice(0, 20).map((event) => {
      const item = document.createElement("article");
      const decision = event.decision === "denied" ? "denied" : "allowed";
      item.className = `audit-card ${decision}`;
      item.innerHTML = `
        <div class="audit-card-main">
          <span class="decision-pill ${decision}">${decision === "denied" ? "! denied" : "allowed"}</span>
          <strong>${escapeHtml(event.command_type ?? event.event_type ?? "api_event")}</strong>
        </div>
        <span class="history-meta">${escapeHtml(formatAuditTime(event.created_at_sec))}</span>
        <span>${escapeHtml(event.operator_id ?? "anonymous")} - ${escapeHtml(event.mission_id ?? "no mission")}</span>
        <span class="history-detail">${escapeHtml(event.reason ?? "No reason recorded")}</span>
        <span class="history-detail">${escapeHtml(event.request_path ?? "")}${formatSourceIp(event.source_ip)}</span>
      `;
      return item;
    }),
  );
}

function renderAuditTimeline(report) {
  const entries = buildAuditTimeline(report);
  elements.reportTimelineCount.textContent = `${entries.length} entries`;

  if (entries.length === 0) {
    elements.reportTimeline.innerHTML = `<li class="empty-event">No report events</li>`;
    return;
  }

  elements.reportTimeline.replaceChildren(
    ...entries.map((entry) => {
      const item = document.createElement("li");
      item.className = `history-item ${entry.category}`;
      item.innerHTML = `
        <span class="history-meta">${escapeHtml(entry.category)} - ${formatStamp(entry.stamp)}</span>
        <strong>${escapeHtml(entry.title)}</strong>
        <span>${escapeHtml(entry.message)}</span>
        ${entry.meta ? `<span class="history-detail">${escapeHtml(entry.meta)}</span>` : ""}
      `;
      return item;
    }),
  );
}

function buildAuditTimeline(report) {
  const commandVerdicts = buildCommandVerdicts(report?.robot_commands ?? [], report?.safety_events ?? []);
  const entries = [];

  (report?.mission_events ?? []).forEach((event) => {
    const details = parseJsonObject(event.details_json);
    entries.push({
      stamp: event.stamp,
      category: "mission",
      title: event.event_type ?? "mission_event",
      message: event.message ?? "",
      meta: [event.step_name, event.target, `operator ${details.operator_id ?? "anonymous"}`]
        .filter(Boolean)
        .join(" - "),
    });
  });

  (report?.robot_commands ?? []).forEach((command) => {
    const verdict = commandVerdicts.get(command.command_id);
    entries.push({
      stamp: command.stamp,
      category: "command",
      title: `${command.command_type ?? "command"} ${command.topic === "robot/command" ? "approved" : "requested"}`,
      message: verdict?.label ?? "No safety verdict recorded",
      meta: [command.command_id, `operator ${command.operator_id ?? operatorFromDetails(command.details_json)}`]
        .filter(Boolean)
        .join(" - "),
    });
  });

  (report?.safety_events ?? []).forEach((event) => {
    entries.push({
      stamp: event.stamp,
      category: "safety",
      title: event.rule ?? "safety_event",
      message: event.message ?? "",
      meta: [
        event.command_id ? `command ${event.command_id}` : "No command link",
        `operator ${event.operator_id ?? "anonymous"}`,
      ].join(" - "),
    });
  });

  (report?.perception_events ?? []).forEach((event) => {
    const artifact = evidenceLabel(event);
    entries.push({
      stamp: event.stamp,
      category: "perception",
      title: event.event_type ?? "perception_event",
      message: `${event.source ?? "sensor"} confidence ${formatRatioPercent(event.confidence)}`,
      meta: artifact,
    });
  });

  (report?.payload_results ?? []).forEach((result) => {
    entries.push({
      stamp: result.stamp,
      category: "payload",
      title: result.result_type ?? "payload_result",
      message: result.summary ?? "",
      meta: `${result.payload_id ?? "payload"} confidence ${formatRatioPercent(result.confidence)}`,
    });
  });

  return entries.sort(compareStampedEntries);
}

function renderEvidencePanels(report) {
  const commandVerdicts = buildCommandVerdicts(report?.robot_commands ?? [], report?.safety_events ?? []);
  const commands = (report?.robot_commands ?? []).map((command) => ({
    title: `${command.command_type ?? "command"} (${command.topic ?? "topic"})`,
    message: commandVerdicts.get(command.command_id)?.label ?? "No safety verdict recorded",
    meta: [command.command_id ?? "No command id", `operator ${command.operator_id ?? operatorFromDetails(command.details_json)}`].join(" - "),
    category: "command",
  }));
  const safety = (report?.safety_events ?? []).map((event) => ({
    title: event.rule ?? "safety_event",
    message: event.message ?? "",
    meta: [
      event.command_id ? `Affected command: ${event.command_id}` : "No command link",
      `operator ${event.operator_id ?? "anonymous"}`,
    ].join(" - "),
    category: "safety",
  }));
  const perception = (report?.perception_events ?? []).map((event) => ({
    title: event.event_type ?? "perception_event",
    message: `${event.source ?? "sensor"} at ${formatPosition(event)}`,
    meta: `${formatRatioPercent(event.confidence)} confidence - ${evidenceLabel(event)}`,
    metaHtml: `${escapeHtml(formatRatioPercent(event.confidence))} confidence - ${artifactLinkHtml(event)}`,
    category: "perception",
  }));
  const payload = (report?.payload_results ?? []).map((result) => ({
    title: result.result_type ?? "payload_result",
    message: result.summary ?? "",
    meta: `${result.payload_id ?? "payload"} - ${formatRatioPercent(result.confidence)} confidence`,
    category: "payload",
  }));

  elements.reportCommandCount.textContent = String(commands.length);
  elements.reportSafetyListCount.textContent = String(safety.length);
  elements.reportPerceptionListCount.textContent = String(perception.length);
  elements.reportPayloadListCount.textContent = String(payload.length);
  renderDetailList(elements.reportCommandList, commands, "No commands");
  renderDetailList(elements.reportSafetyList, safety, "No safety events");
  renderDetailList(elements.reportPerceptionList, perception, "No perception events");
  renderDetailList(elements.reportPayloadList, payload, "No payload results");
}

function renderDetailList(element, entries, emptyMessage) {
  if (entries.length === 0) {
    element.innerHTML = `<li class="empty-event">${escapeHtml(emptyMessage)}</li>`;
    return;
  }

  element.replaceChildren(
    ...entries.map((entry) => {
      const item = document.createElement("li");
      item.className = `history-item ${entry.category}`;
      item.innerHTML = `
        <strong>${escapeHtml(entry.title)}</strong>
        <span>${escapeHtml(entry.message)}</span>
        <span class="history-detail">${entry.metaHtml ?? escapeHtml(entry.meta)}</span>
      `;
      return item;
    }),
  );
}

function buildCommandVerdicts(commands, safetyEvents) {
  const byCommand = new Map();
  commands.forEach((command) => {
    if (!command.command_id) {
      return;
    }
    const verdict = byCommand.get(command.command_id) ?? { hasApproval: false, safetyEvents: [] };
    if (command.topic === "robot/command") {
      verdict.hasApproval = true;
    }
    byCommand.set(command.command_id, verdict);
  });

  safetyEvents.forEach((event) => {
    if (!event.command_id) {
      return;
    }
    const verdict = byCommand.get(event.command_id) ?? { hasApproval: false, safetyEvents: [] };
    verdict.safetyEvents.push(event);
    byCommand.set(event.command_id, verdict);
  });

  byCommand.forEach((verdict) => {
    const blocked = verdict.safetyEvents.find((event) => event.command_blocked);
    const adjusted = verdict.safetyEvents.find((event) => !event.command_blocked);
    if (blocked) {
      verdict.label = `Blocked by ${blocked.rule}: ${blocked.message}`;
    } else if (adjusted && verdict.hasApproval) {
      verdict.label = `Approved with safety note ${adjusted.rule}: ${adjusted.message}`;
    } else if (verdict.hasApproval) {
      verdict.label = "Approved by safety gate";
    } else if (adjusted) {
      verdict.label = `Safety note ${adjusted.rule}: ${adjusted.message}`;
    } else {
      verdict.label = "Requested; no approval observed";
    }
  });

  return byCommand;
}

function reportSector(report) {
  const missionSector = report?.mission?.sector;
  if (missionSector) {
    return missionSector;
  }

  for (const event of report?.mission_events ?? []) {
    const details = parseJsonObject(event.details_json);
    if (details.sector) {
      return details.sector;
    }
  }
  return "No data";
}

function evidenceLabel(event) {
  const parts = [];
  if (event?.evidence_artifact_url) {
    parts.push(`artifact ${event.evidence_artifact_url}`);
  }
  if (event?.evidence_hash) {
    parts.push(`hash ${shortenHash(event.evidence_hash)}`);
  }
  return parts.length > 0 ? parts.join(" - ") : "No artifact captured";
}

function artifactLinkHtml(event) {
  if (!event?.evidence_artifact_url) {
    return "No artifact captured";
  }

  const href = String(event.evidence_artifact_url);
  if (!href.startsWith("/artifacts/")) {
    return escapeHtml(evidenceLabel(event));
  }

  const hashText = event.evidence_hash ? ` hash ${shortenHash(event.evidence_hash)}` : "";
  return `<a class="artifact-link" href="${escapeHtml(href)}">${escapeHtml(href)}</a>${escapeHtml(hashText)}`;
}

function formatPosition(event) {
  return `x ${formatNumber(event?.x)}, y ${formatNumber(event?.y)}, z ${formatNumber(event?.z)}`;
}

function compareStampedEntries(left, right) {
  const leftStamp = Number(left.stamp?.sec ?? 0) + Number(left.stamp?.nanosec ?? 0) / 1_000_000_000;
  const rightStamp = Number(right.stamp?.sec ?? 0) + Number(right.stamp?.nanosec ?? 0) / 1_000_000_000;
  return leftStamp - rightStamp;
}

async function copyReportHash() {
  const hash = state.latestReport?.content_hash;
  if (!hash) {
    elements.reportStatus.textContent = "No hash available to copy";
    return;
  }
  try {
    await navigator.clipboard.writeText(hash);
    elements.reportStatus.textContent = "Report hash copied";
  } catch (error) {
    elements.reportStatus.textContent = "Could not copy report hash";
  }
}

function exportSelectedReport() {
  if (!state.selectedReportId) {
    elements.reportStatus.textContent = "Select a report to export";
    return;
  }

  window.location.href = `/reports/${encodeURIComponent(state.selectedReportId)}/export`;
}

function exportSelectedReportBundle() {
  if (!state.selectedReportId) {
    elements.reportStatus.textContent = "Select a report to export";
    return;
  }

  window.location.href = `/reports/${encodeURIComponent(state.selectedReportId)}/export-bundle`;
}

function operatorId() {
  const value = elements.operatorId.value.trim();
  return value || "anonymous";
}

function operatorFromDetails(detailsJson) {
  const details = parseJsonObject(detailsJson);
  return details.operator_id || "anonymous";
}

function syncCommandButtons() {
  setCommandButtonsDisabled(!state.selectedMissionId);
}

function setCommandButtonsDisabled(disabled) {
  elements.commandButtons.forEach((button) => {
    button.disabled = disabled;
  });
}

function setStatus(element, label, statusClass) {
  element.textContent = label;
  element.classList.remove("ok", "warn", "error", "pending");
  element.classList.add(statusClass);
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, {
    headers: { Accept: "application/json" },
    ...options,
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail ?? data);
    throw new Error(detail || `Request failed: ${response.status}`);
  }

  return data;
}

function missionStateClass(value) {
  if (["running", "completed"].includes(value)) {
    return "ok";
  }
  if (["paused", "idle", "ready", "reset"].includes(value)) {
    return "warn";
  }
  if (["canceled", "failed", "error"].includes(value)) {
    return "error";
  }
  return "pending";
}

function formatPercent(value) {
  if (value === undefined || value === null || Number.isNaN(Number(value))) {
    return "No data";
  }
  return `${Math.round(Number(value))}%`;
}

function formatRatioPercent(value) {
  if (value === undefined || value === null || Number.isNaN(Number(value))) {
    return "No data";
  }
  return `${Math.round(Number(value) * 100)}%`;
}

function formatPose(pose) {
  if (!pose) {
    return "No data";
  }
  return `x ${formatNumber(pose.x)}, y ${formatNumber(pose.y)}, yaw ${formatNumber(pose.yaw)}`;
}

function formatNumber(value) {
  if (value === undefined || value === null || Number.isNaN(Number(value))) {
    return "0.00";
  }
  return Number(value).toFixed(2);
}

function formatStamp(stamp) {
  if (!stamp || stamp.sec === undefined) {
    return "--:--:--";
  }

  return new Date(Number(stamp.sec) * 1000).toLocaleTimeString();
}

function formatAuditTime(sec) {
  if (sec === undefined || sec === null || Number.isNaN(Number(sec))) {
    return "--:--:--";
  }
  return new Date(Number(sec) * 1000).toLocaleString();
}

function formatSourceIp(sourceIp) {
  return sourceIp ? ` - ${sourceIp}` : "";
}

function shortenHash(value) {
  if (!value) {
    return "No data";
  }
  return value.length > 16 ? `${value.slice(0, 16)}...` : value;
}

function parseJsonObject(value) {
  try {
    const parsed = JSON.parse(value);
    return parsed && typeof parsed === "object" && !Array.isArray(parsed) ? parsed : {};
  } catch (error) {
    return {};
  }
}

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}

function debounce(callback, waitMs) {
  let timeoutId;
  return (...args) => {
    window.clearTimeout(timeoutId);
    timeoutId = window.setTimeout(() => callback(...args), waitMs);
  };
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
