import heapq
from collections import defaultdict
from statistics import mean
from typing import Iterator, List, TypedDict

from log_analyzer.parsing import LogEntry


class UrlStats(TypedDict):
    url: str
    count: int
    time_sum: float
    time_perc: float
    time_avg: float
    time_max: float
    time_med: float


UrlRunningStats = TypedDict("UrlRunningStats", {"items": List[float], "time_sum": float})


class LogStats:
    def __init__(self) -> None:
        self.stats: dict[str, UrlRunningStats] = defaultdict(lambda: {"items": [], "time_sum": 0.0})
        self.total_time = 0.0

    def consume_log_iter(self, it: Iterator[LogEntry]) -> None:
        for log_entry in it:
            e = self.stats[log_entry.url]
            e["items"].append(log_entry.request_time)
            e["time_sum"] += log_entry.request_time
            self.total_time += log_entry.request_time

    def _compute_final_url_stats(self, url: str, s: UrlRunningStats) -> UrlStats:
        s["items"].sort()
        non_empty = len(s["items"]) > 0

        return {
            "url": url,
            "count": len(s["items"]),
            "time_sum": round(s["time_sum"], 3),
            "time_avg": round(mean(s["items"]), 3) if non_empty else 0,
            "time_max": round(s["items"][-1], 3) if non_empty else 0,
            "time_med": round(s["items"][len(s["items"]) // 2], 3) if non_empty else 0,
            "time_perc": round(s["time_sum"] / self.total_time, 3) if self.total_time > 0 else 0,
        }

    def top_urls_report(self, n: int) -> List[UrlStats]:
        # _heapq.nlargest(n, self.iteritems(), key=_itemgetter(1))
        top_urls = heapq.nlargest(n, self.stats.items(), key=lambda x: x[1]["time_sum"])
        return [self._compute_final_url_stats(url, stats) for url, stats in top_urls]
