import re
from collections import namedtuple

lineformat = re.compile(
    r"""
   (?P<remote_addr>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s+
   (?P<remote_user>(.+?))\s+
   (?P<real_ip>(.+?))\s+
   \[(?P<dateandtime>\d{2}\/[a-z]{3}\/\d{4}:\d{2}:\d{2}:\d{2}\s(\+|\-)\d{4})\]\s+
   ((\"(GET|POST)\s)(?P<url>.+)\s(http\/\d\.\d"))\s+
   (?P<status>\d{3})\s+
   (?P<bytes_Sent>\d+)\s+
   (["](?P<refferer>(\-)|(.+))["])\s+
   (["](?P<useragent>.+)["])\s+
   (["](?P<http_x_forwarded_for>.+)["])\s+
   (["](?P<http_x_request_id>.+)["])\s+
   (["](?P<http_x_rb_user>.+)["])\s+
   (?P<request_time>.+)
#    "-"\s+
#    "(?P<x_forwaded_for>(.+?))"\s+
#    "(?P<http_x_request_id>(.+?))"\s+
#    "(?P<http_xb_user>(.+?))"\s+
#    (?P<request_time>[+-]?([0-9]*[.])?[0-9]+)
   """,
    re.IGNORECASE | re.VERBOSE,
)

LogEntry = namedtuple("LogEntry", ["url", "request_time"])


def parse_log_line(line: str) -> dict[str, str]:
    data = re.search(lineformat, line)
    if not data:
        raise ValueError(f"unable to parse line given: {line}")
    return data.groupdict()
