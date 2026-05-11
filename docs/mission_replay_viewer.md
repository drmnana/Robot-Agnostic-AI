# Mission Replay Viewer

## Purpose

Mission Replay turns a persisted mission report into a chronological sequence of frames that an operator can play, scrub, filter, and share.

It is the narrative companion to the forensic report drilldown. The replay does not create new facts; it normalizes the existing mission report, command, safety, perception, and payload records into one playback stream.

## Backend API

```text
GET /reports/{report_id}/replay
```

Optional filters:

- `category`
- `since`
- `operator_id`
- `command_id`

Replay frames include:

- `frame_index`
- `timestamp_sec`
- `category`
- `title`
- `message`
- `operator_id`
- `command_id`
- `artifact_url`
- `artifact_hash`
- `source_id`

Frames are sorted by timestamp and re-indexed after filters are applied.

## Dashboard Controls

The dashboard Mission History view includes a Mission Replay panel with:

- play and pause
- previous and next frame
- jump to next event
- scrubber slider
- playback speed presets: `1x`, `2x`, `4x`, `10x`
- frame-specific styling for mission, command, safety, perception, and payload frames

## URL Addressing

Replay position is URL-addressable:

```text
/dashboard/?frame=3
/dashboard/?t=1778483505
```

`frame` restores a specific replay frame index. `t` restores the first frame at or after the requested timestamp.

## Cross References

Replay frames preserve links back to the underlying audit record when available:

- safety frames preserve `command_id`
- command frames preserve `command_id`
- perception frames preserve `artifact_url` and `artifact_hash`
