const state = {
  missions: [],
  selectedMissionId: null,
  selectedReportId: null,
  runtime: null,
  latestReport: null,
  reports: [],
};

const elements = {
  backendStatus: document.querySelector("#backend-status"),
  bridgeStatus: document.querySelector("#bridge-status"),
  lastUpdated: document.querySelector("#last-updated"),
  missionList: document.querySelector("#mission-list"),
  selectedMissionLabel: document.querySelector("#selected-mission-label"),
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
  reportMission: document.querySelector("#report-mission"),
  reportState: document.querySelector("#report-state"),
  reportMissionEvents: document.querySelector("#report-mission-events"),
  reportPayloadResults: document.querySelector("#report-payload-results"),
  reportPerceptionEvents: document.querySelector("#report-perception-events"),
  reportSafetyEvents: document.querySelector("#report-safety-events"),
  reportHash: document.querySelector("#report-hash"),
  reportTimeline: document.querySelector("#report-timeline"),
};

elements.refreshButton.addEventListener("click", () => refreshAll());
elements.reportRefreshButton.addEventListener("click", () => refreshLatestReport());
elements.reportFilterClear.addEventListener("click", () => clearReportFilters());
[
  elements.reportFilterOutcome,
  elements.reportFilterDateFrom,
  elements.reportFilterDateTo,
  elements.reportFilterSafety,
  elements.reportFilterBlocked,
].forEach((control) => {
  control.addEventListener("change", () => refreshLatestReport({ resetSelection: true }));
});
[elements.reportFilterMission, elements.reportFilterSector, elements.reportFilterPerception].forEach((control) => {
  control.addEventListener("input", debounce(() => refreshLatestReport({ resetSelection: true }), 350));
});
elements.commandButtons.forEach((button) => {
  button.addEventListener("click", () => sendMissionCommand(button.dataset.command));
});

refreshAll();
setInterval(refreshRuntime, 2000);

async function refreshAll() {
  await Promise.all([refreshMissions(), refreshRuntime(), refreshLatestReport()]);
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
    });
    elements.commandMessage.textContent = `${response.command_type} accepted for ${response.mission_id}`;
    await refreshRuntime();
    if (["cancel", "reset", "start"].includes(response.command_type)) {
      await refreshLatestReport();
    }
  } catch (error) {
    elements.commandMessage.textContent = error.message;
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
  elements.reportMission.textContent = mission?.name ?? mission?.mission_id ?? "No data";
  elements.reportState.textContent = mission?.state ?? "No data";
  elements.reportMissionEvents.textContent = String(missionEvents.length);
  elements.reportPayloadResults.textContent = String(payloadResults.length);
  elements.reportPerceptionEvents.textContent = String(perceptionEvents.length);
  elements.reportSafetyEvents.textContent = String(safetyEvents.length);
  elements.reportHash.textContent = shortenHash(report?.content_hash);
  renderReportTimeline(missionEvents);
}

function renderReportUnavailable(message) {
  elements.reportStatus.textContent = message || "Mission report not found";
  elements.reportList.innerHTML = `<div class="message-line">No reports available.</div>`;
  elements.reportMission.textContent = "No data";
  elements.reportState.textContent = "No data";
  elements.reportMissionEvents.textContent = "0";
  elements.reportPayloadResults.textContent = "0";
  elements.reportPerceptionEvents.textContent = "0";
  elements.reportSafetyEvents.textContent = "0";
  elements.reportHash.textContent = "No data";
  elements.reportTimeline.innerHTML = `<li class="empty-event">No report yet</li>`;
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
      });
      return button;
    }),
  );
}

function renderReportTimeline(missionEvents) {
  const recentEvents = [...missionEvents].slice(-10).reverse();
  if (recentEvents.length === 0) {
    elements.reportTimeline.innerHTML = `<li class="empty-event">No report events</li>`;
    return;
  }

  elements.reportTimeline.replaceChildren(
    ...recentEvents.map((event) => {
      const item = document.createElement("li");
      item.className = "history-item mission";
      item.innerHTML = `
        <span class="history-meta">report - ${formatStamp(event.stamp)}</span>
        <strong>${escapeHtml(event.event_type ?? "event")}</strong>
        <span>${escapeHtml(event.message ?? "")}</span>
      `;
      return item;
    }),
  );
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

function shortenHash(value) {
  if (!value) {
    return "No data";
  }
  return value.length > 16 ? `${value.slice(0, 16)}...` : value;
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
