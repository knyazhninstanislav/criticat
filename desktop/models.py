from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Settings:
    db_path: str = "criticat.db"
    check_interval: int = 5  # минуты
    threshold_percent: float = 0  # Больше не используется
    monitored_tests: List[str] = None

    def __post_init__(self):
        if self.monitored_tests is None:
            self.monitored_tests = []


@dataclass
class LabResult:
    id: int
    ids: int
    full_name: str
    test_name: str
    result_value: float
    ref_upper: Optional[float]
    ref_lower: Optional[float]

    def get_ref_range_str(self) -> str:
        if self.ref_lower is not None and self.ref_upper is not None:
            return f"{self.ref_lower} - {self.ref_upper}"
        return "Не указаны"