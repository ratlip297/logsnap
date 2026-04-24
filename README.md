# logsnap

> A CLI tool to capture, filter, and snapshot structured logs from multiple services into a single timestamped archive.

---

## Installation

```bash
pip install logsnap
```

Or install from source:

```bash
git clone https://github.com/yourname/logsnap.git && cd logsnap && pip install .
```

---

## Usage

Capture logs from one or more services and save a timestamped snapshot:

```bash
logsnap capture --services web api worker --output ./snapshots
```

Filter logs by level or keyword before archiving:

```bash
logsnap capture --services web --filter level=ERROR --filter keyword="timeout"
```

List existing snapshots:

```bash
logsnap list ./snapshots
```

Inspect a specific snapshot:

```bash
logsnap inspect ./snapshots/snapshot_20240915_143022.tar.gz
```

### Options

| Flag | Description |
|------|-------------|
| `--services` | One or more service names to capture logs from |
| `--filter` | Filter expression (e.g. `level=ERROR`, `keyword=timeout`) |
| `--output` | Directory to write the snapshot archive |
| `--format` | Log format: `json` (default) or `text` |
| `--since` | Capture logs since a relative time (e.g. `1h`, `30m`) |

---

## Requirements

- Python 3.8+
- Services must emit structured logs to `stdout` or a configurable log path

---

## License

This project is licensed under the [MIT License](LICENSE).