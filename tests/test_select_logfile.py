from datetime import datetime
from pathlib import Path

from log_analyzer.main import select_logfile


def test_select_log_file():
    candidates = map(
        lambda x: Path("results") / x,
        [
            "nginx-access-ui.log-20170629.gz",
            "nginx-access-ui.log-20170630.gz",
            "nginx-access-ui.log-20170631.gz",  # invalid date
            "nginx-access-ui.log-201706291.gz",
            "nginx-access-ui.log-20170630.bz2" "nginx-access-main.log-20170630.gz",
        ],
    )

    selected = select_logfile(candidates)

    assert selected is not None
    assert selected[0] == Path("results/nginx-access-ui.log-20170630.gz")
    assert selected[1] == datetime(2017, 6, 30)
