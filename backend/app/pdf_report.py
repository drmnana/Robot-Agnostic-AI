from datetime import datetime, timezone
from typing import Iterable

from .event_severity import (
    severity_for_mission_event,
    severity_for_payload_result,
    severity_for_perception_event,
    severity_for_robot_command,
    severity_for_safety_event,
)


PAGE_WIDTH = 612
PAGE_HEIGHT = 792
LEFT = 54
TOP = 742
LINE_HEIGHT = 15
MAX_LINES = 43


def build_report_pdf(report: dict, evidence_package: dict) -> bytes:
    report_id = report.get("report_id", "unknown-report")
    evidence_hash = evidence_package.get("export_hash", "")
    lines = build_pdf_lines(report, evidence_package)
    pages = paginate(lines)
    page_streams = [
        render_page(page_lines, page_index + 1, len(pages), report_id, evidence_hash)
        for page_index, page_lines in enumerate(pages)
    ]
    return assemble_pdf(page_streams)


def build_pdf_lines(report: dict, evidence_package: dict) -> list[tuple[str, int]]:
    mission = report.get("mission") or {}
    summary = evidence_package.get("summary") or {}
    evidence_hash = evidence_package.get("export_hash", "")
    content_hash = report.get("content_hash", "")
    lines: list[tuple[str, int]] = [
        ("ORIMUS Mission Report Summary", 18),
        ("", 11),
        (
            "This PDF is a human-readable summary. The authoritative machine-readable "
            f"record is the JSON Evidence Package (SHA-256: {evidence_hash}).",
            10,
        ),
        (
            "To verify integrity, retrieve the JSON package and run "
            "verify_evidence_package.py.",
            10,
        ),
        ("", 11),
        (f"Report ID: {report.get('report_id', '')}", 11),
        (f"Mission: {mission.get('name', '')} ({mission.get('mission_id', '')})", 11),
        (f"Sector: {mission.get('sector', '')}", 11),
        (f"Outcome: {mission.get('state', '')}", 11),
        (f"Generated: {datetime.now(timezone.utc).isoformat()}", 11),
        (f"Mission Report Content Hash: {content_hash}", 9),
        (f"JSON Evidence Package SHA-256: {evidence_hash}", 9),
        ("", 11),
        ("Event Counts", 14),
        (f"Mission states: {summary.get('mission_state_count', 0)}", 10),
        (f"Mission events: {summary.get('mission_event_count', 0)}", 10),
        (f"Robot commands: {summary.get('robot_command_count', 0)}", 10),
        (f"Safety events: {summary.get('safety_event_count', 0)}", 10),
        (f"Perception events: {summary.get('perception_event_count', 0)}", 10),
        (f"Payload results: {summary.get('payload_result_count', 0)}", 10),
        ("", 11),
        ("Severity-Labeled Timeline", 14),
    ]
    for item in timeline_entries(report):
        lines.append((item, 9))
    lines.extend(section_lines("Commands", command_lines(report)))
    lines.extend(section_lines("Safety", safety_lines(report)))
    lines.extend(section_lines("Perception", perception_lines(report)))
    lines.extend(section_lines("Payload Results", payload_lines(report)))
    return flatten_wrapped_lines(lines)


def section_lines(title: str, items: Iterable[str]) -> list[tuple[str, int]]:
    lines = [("", 11), (title, 14)]
    entries = list(items)
    if not entries:
        lines.append(("No records", 9))
    else:
        lines.extend((entry, 9) for entry in entries)
    return lines


def timeline_entries(report: dict) -> list[str]:
    entries = []
    for event in report.get("mission_events", []):
        entries.append(
            timeline_line(event.get("stamp"), severity_for_mission_event(event).value, "mission", event.get("event_type"), event.get("message"))
        )
    for command in report.get("robot_commands", []):
        entries.append(
            timeline_line(command.get("stamp"), severity_for_robot_command(command).value, "command", command.get("command_type"), command.get("command_id"))
        )
    for event in report.get("safety_events", []):
        entries.append(
            timeline_line(event.get("stamp"), severity_for_safety_event(event).value, "safety", event.get("rule"), event.get("message"))
        )
    for event in report.get("perception_events", []):
        entries.append(
            timeline_line(event.get("stamp"), severity_for_perception_event(event).value, "perception", event.get("event_type"), event.get("source"))
        )
    for result in report.get("payload_results", []):
        entries.append(
            timeline_line(result.get("stamp"), severity_for_payload_result(result).value, "payload", result.get("result_type"), result.get("summary"))
        )
    return sorted(entries)


def timeline_line(stamp: dict | None, severity: str, category: str, title: str | None, message: str | None) -> str:
    return f"{stamp_label(stamp)} [{severity}] {category}: {title or ''} {message or ''}".strip()


def command_lines(report: dict) -> list[str]:
    return [
        f"[{severity_for_robot_command(command).value}] {command.get('command_type', '')} {command.get('command_id', '')} operator={command.get('operator_id', '')}"
        for command in report.get("robot_commands", [])
    ]


def safety_lines(report: dict) -> list[str]:
    return [
        f"[{severity_for_safety_event(event).value}] {event.get('rule', '')} command={event.get('command_id', '')} blocked={event.get('command_blocked')} {event.get('message', '')}"
        for event in report.get("safety_events", [])
    ]


def perception_lines(report: dict) -> list[str]:
    lines = []
    for event in report.get("perception_events", []):
        artifact = event.get("evidence_artifact_url") or "no artifact"
        lines.append(
            f"[{severity_for_perception_event(event).value}] {event.get('event_type', '')} source={event.get('source', '')} artifact={artifact} hash={event.get('evidence_hash') or ''}"
        )
    return lines


def payload_lines(report: dict) -> list[str]:
    return [
        f"[{severity_for_payload_result(result).value}] {result.get('result_type', '')} {result.get('payload_id', '')} {result.get('summary', '')}"
        for result in report.get("payload_results", [])
    ]


def flatten_wrapped_lines(lines: list[tuple[str, int]]) -> list[tuple[str, int]]:
    flattened = []
    for text, size in lines:
        if not text:
            flattened.append((text, size))
            continue
        chunks = wrap_text(text, 92 if size < 12 else 72)
        flattened.extend((chunk, size) for chunk in chunks)
    return flattened


def wrap_text(text: str, max_chars: int) -> list[str]:
    words = text.split()
    lines = []
    current = ""
    for word in words:
        if len(current) + len(word) + 1 > max_chars:
            lines.append(current)
            current = word
        else:
            current = f"{current} {word}".strip()
    if current:
        lines.append(current)
    return lines or [""]


def paginate(lines: list[tuple[str, int]]) -> list[list[tuple[str, int]]]:
    return [lines[index:index + MAX_LINES] for index in range(0, len(lines), MAX_LINES)] or [[("", 11)]]


def render_page(
    lines: list[tuple[str, int]],
    page_number: int,
    page_count: int,
    report_id: str,
    evidence_hash: str,
) -> str:
    commands = ["BT", "/F1 11 Tf", f"{LEFT} {TOP} Td"]
    cursor_size = 11
    for text, size in lines:
        if size != cursor_size:
            commands.append(f"/F1 {size} Tf")
            cursor_size = size
        commands.append(f"({escape_pdf_text(text)}) Tj")
        commands.append(f"0 -{LINE_HEIGHT} Td")
    footer = f"Report {report_id} | Evidence Package SHA-256: {evidence_hash} | Page {page_number} of {page_count}"
    commands.extend([
        "ET",
        "BT",
        "/F1 7 Tf",
        f"{LEFT} 34 Td",
        f"({escape_pdf_text(footer)}) Tj",
        "ET",
    ])
    return "\n".join(commands)


def assemble_pdf(page_streams: list[str]) -> bytes:
    objects = []
    page_object_numbers = []
    objects.append("<< /Type /Catalog /Pages 2 0 R >>")
    objects.append("__PAGES__")
    objects.append("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    for stream in page_streams:
        content_object_number = len(objects) + 1
        stream_bytes = stream.encode("latin-1", errors="replace")
        objects.append(f"<< /Length {len(stream_bytes)} >>\nstream\n{stream}\nendstream")
        page_object_number = len(objects) + 1
        page_object_numbers.append(page_object_number)
        objects.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {PAGE_WIDTH} {PAGE_HEIGHT}] "
            f"/Resources << /Font << /F1 3 0 R >> >> /Contents {content_object_number} 0 R >>"
        )

    kids = " ".join(f"{number} 0 R" for number in page_object_numbers)
    objects[1] = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_object_numbers)} >>"

    output = "%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
    offsets = []
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(output.encode("latin-1", errors="replace")))
        output += f"{index} 0 obj\n{obj}\nendobj\n"
    xref_offset = len(output.encode("latin-1", errors="replace"))
    output += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n"
    for offset in offsets:
        output += f"{offset:010d} 00000 n \n"
    output += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n"
    return output.encode("latin-1", errors="replace")


def stamp_label(stamp: dict | None) -> str:
    if not isinstance(stamp, dict):
        return "t=0"
    sec = stamp.get("sec", 0)
    nanosec = stamp.get("nanosec", 0)
    return f"t={sec}.{int(nanosec):09d}"


def escape_pdf_text(text: str) -> str:
    return str(text).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
