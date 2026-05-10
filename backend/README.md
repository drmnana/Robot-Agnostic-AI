# ORIMUS Backend

This backend exposes HTTP APIs for ORIMUS operator tools.

The first version is intentionally small:

- Health check
- List mission YAML configs
- Read a mission YAML config
- Read the latest mission report
- Forward mission start, pause, resume, and cancel commands
- Forward live runtime state from the ROS mission API bridge
- Serve the first operator dashboard prototype from `/dashboard/`

ROS 2 integration is currently routed through the `mission_api_bridge` package.
