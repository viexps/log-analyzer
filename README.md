# log analyzer

## Setup

Project requires Poetry. ([installation instructions](https://python-poetry.org/docs/#installation))

Lower boundary on Python version is set to `3.10`

```bash
poetry shell
poetry install
```

## Testing

```bash
pytest
```

## Running main script

```bash
python log_analyzer/main.py
```

Default location of config file: `./config/config.json`

Config location can be overriddeden with `--config` argument

```bash
python log_analyzer/main.py --config my_config.json
```

### Default config values

```python
{
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log",  # directory with nginx log files
    "LOGGING_LEVEL": "INFO",
    "LOGGING_FILE": None,
}
```
