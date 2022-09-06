#!/usr/bin/env python
# -*- coding: utf-8 -*-


# log_format ui_short '$remote_addr  $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';

import argparse
import gzip
import json
import logging
import re
import string
from datetime import datetime
from operator import itemgetter
from pathlib import Path
from typing import Any, Iterator, List, cast

from log_analyzer import parsing
from log_analyzer.stats import LogStats, UrlStats

config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log",  # directory with nginx log files
    "LOGGING_LEVEL": "INFO",
    "LOGGING_FILE": None,
}


def log_lines(path: Path, error_threshold: float) -> Iterator[parsing.LogEntry]:
    with gzip.open(path, mode="rt", encoding="utf-8") as file:
        num_processed = 0
        num_errors = 0
        for line in file:
            # print(line)
            try:
                data = parsing.parse_log_line(line)
                num_processed += 1

                yield parsing.LogEntry(data["url"], float(data["request_time"]))
            except ValueError:
                num_errors += 1

    logging.info("num processed: %d", num_processed)
    logging.info("num errors: %s", num_errors)
    error_ratio = num_errors / num_processed if num_processed > 0 else 0.0
    if error_ratio > error_threshold:
        raise Exception("error threshold exceeded: %f" % error_threshold)


def setup_logging(logging_filename: str | None, loglevel: str) -> None:
    numeric_loglevel = getattr(logging, loglevel.upper(), None)
    if not isinstance(numeric_loglevel, int):
        raise ValueError(f"Invalid log level: {loglevel}")

    log_filename = Path(logging_filename) if logging_filename else None
    logging.basicConfig(
        filename=log_filename,
        format="[%(asctime)s] %(levelname).1s %(message)s",
        level=numeric_loglevel,
        datefmt="%Y.%m.%d %H:%M:%S",
    )


def select_logfile(files: Iterator[Path]) -> tuple[Path, datetime] | None:

    validated: List[tuple[Path, datetime]] = []
    for f in files:
        match = re.search(r"(\d+)", str(f))
        if match:
            date_str = match.group(1)
            try:
                dt = datetime.strptime(date_str, "%Y%m%d")
                validated.append((f, dt))
            except ValueError:
                logging.debug("unable to extract date from path: {}", f)
        else:
            logging.debug("unable to extract date from path: {}", f)

    if not validated:
        return None
    else:
        return sorted(validated, key=itemgetter(1), reverse=True)[0]


def read_template() -> string.Template:
    template_path = Path("templates/report.html")
    if not template_path.exists() or not template_path.is_file():
        raise ValueError("template file not found")

    with open(template_path, "r", encoding="utf-8") as f:
        template = string.Template(f.read())

    return template


def result_file_path(result_dir: Path, log_date: datetime) -> Path:
    filename = datetime.strftime(log_date, "report-%Y.%m.%d.html")
    return result_dir / filename


def write_template(tpl: string.Template, report: List[UrlStats], result_file_path: Path) -> None:

    table_json = json.dumps(report)
    report_html = tpl.safe_substitute({"table_json": table_json})

    with open(result_file_path, "w", encoding="utf-8") as out:
        out.write(report_html)


def load_config() -> dict[str, Any]:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", help="path to config file", default="./config/config.json")
    args = parser.parse_args()

    config_path = Path(args.config)

    if not config_path.exists():
        raise ValueError(f"config file not found on path: {config_path}")

    with open(config_path) as f:
        provided_config = json.load(f)

    return config | provided_config


def main() -> None:
    conf = load_config()
    setup_logging(
        logging_filename=str(conf["LOGGING_FILE"]) if conf.get("LOGGING_FILE") else None,
        loglevel=str(conf["LOGGING_LEVEL"]),
    )
    logging.info("resolved config: %s", conf)

    log_dir = Path(str(conf["LOG_DIR"]))
    if not log_dir.is_dir():
        raise ValueError("LOG_DIR parameter should refer to a directory.")

    # selecting latest log file and extracting date
    access_log_glob = "nginx-access-ui.log-[0-9]*.gz"
    selected_file = select_logfile(log_dir.glob(access_log_glob))

    if not selected_file:
        logging.info("can't find any log files matching criteria. exiting...")
        return

    most_recent_log = selected_file[0]
    log_date = selected_file[1]

    template = read_template()

    result_fpath = result_file_path(Path(str(conf["REPORT_DIR"])), log_date)
    if result_fpath.exists():
        logging.info("result report already exists under path: %s. exiting...", str(result_fpath))
        return

    log_gen = log_lines(most_recent_log, error_threshold=0.01)

    # read log lines and accumulate statistics
    stats = LogStats()
    stats.consume_log_iter(log_gen)

    # calculate final statistics for urls with largest accumulated resp times
    top_urls_stats = stats.top_urls_report(cast(int, conf["REPORT_SIZE"]))

    write_template(template, top_urls_stats, result_fpath)

    logging.info("complete")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.exception(e, exc_info=True)
