# Incident Timeline

| Time | Event | Evidence |
| :--- | :--- | :--- |
| **16:45:00 UTC** | Healthy baseline confirmed | [baseline.md](baseline.md) |
| **16:45:22 UTC** | Failure simulation started | [failure.md](failure.md) |
| **16:45:22 UTC** | Database connectivity lost | [failure.md](failure.md) |
| **16:45:25 UTC** | Readiness changed (ready -> 503) | [failure.md](failure.md) |
| **16:45:37 UTC** | Alert entered firing state (`APIUnavailable`) | [failure.md](failure.md) |
| **16:46:10 UTC** | Database restored (`docker compose start db`) | [recovery.md](recovery.md) |
| **16:46:22 UTC** | Readiness recovered (ready -> 200) | [recovery.md](recovery.md) |
| **16:46:37 UTC** | Alert cleared (firing -> inactive) | [recovery.md](recovery.md) |
| **16:46:38 UTC** | Successful validation performed | [recovery.md](recovery.md) |
