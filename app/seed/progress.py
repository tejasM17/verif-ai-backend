import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

try:
    from tqdm import tqdm
    _HAS_TQDM = True
except ImportError:
    _HAS_TQDM = False


@dataclass
class ProgressBar:
    total: int
    desc: str = ""
    unit: str = "doc"

    def __post_init__(self) -> None:
        self._start = time.monotonic()
        self._last_pct = -1
        self._bar = None
        self._done = 0
        if _HAS_TQDM:
            self._bar = tqdm(
                total=self.total,
                desc=self.desc,
                unit=self.unit,
                file=sys.stderr,
                dynamic_ncols=True,
            )

    def update(self, n: int = 1) -> None:
        if self._bar is not None:
            self._bar.update(n)
            self._done += n
            return
        self._done += n
        pct = int((self._done / max(self.total, 1)) * 100)
        if pct >= self._last_pct + 5:
            self._last_pct = pct
            eta = self._estimate_eta(self._done)
            sys.stderr.write(f"\r{self.desc} {pct}% ({self._done}/{self.total}) {eta}")
            sys.stderr.flush()

    def _estimate_eta(self, done: int) -> str:
        elapsed = time.monotonic() - self._start
        if done <= 0:
            return "eta=--:--"
        rate = done / max(elapsed, 0.001)
        remaining = max(self.total - done, 0)
        eta_s = remaining / max(rate, 0.001)
        return f"eta={int(eta_s // 60):02d}:{int(eta_s % 60):02d} ({rate:.0f} {self.unit}/s)"

    def close(self) -> None:
        if self._bar is not None:
            self._bar.close()
        else:
            sys.stderr.write("\n")
            sys.stderr.flush()


def fmt_timestamp(dt: Optional[datetime] = None) -> str:
    if dt is None:
        dt = datetime.now(timezone.utc)
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")


__all__ = ["ProgressBar", "fmt_timestamp"]
