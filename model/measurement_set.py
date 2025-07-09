from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import json


@dataclass
class ChannelCurve:
    channel: str  # "R", "G", "B", etc...
    values: List[float]  # 21 density points


@dataclass
class MeasurementSet:
    path: Path
    date: datetime
    curves: Dict[str, ChannelCurve]
    name: Optional[str] = None
    color: Optional[str] = None

    @classmethod
    def load_from_file(cls, path: Path) -> Optional["MeasurementSet"]:
        if not cls._is_valid_file(path):
            print(f"Invalid file ignored : {path.name}")
            return None

        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            name = data.get("name")
            color = data.get("color")
            json_date = data.get("date")

            values_dict = data.get("values", {})
            curves = {
                ch.upper(): ChannelCurve(channel=ch.upper(), values=vals)
                for ch, vals in values_dict.items()
                if isinstance(vals, list) and len(vals) == 21
            }

            if not curves:
                print(f"No valid curves found in : {path.name}")
                return None

            date = cls._parse_date(json_date, path.stat().st_mtime)

            return cls(path=path, name=name, color=color, date=date, curves=curves)

        except Exception as e:
            print(f"Error when loading {path.name} : {e}")
            return None

    @staticmethod
    def _is_valid_file(path: Path) -> bool:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            values = data.get("values", {})
            if not isinstance(values, dict):
                return False
            if not any(isinstance(v, list) and len(v) == 21 for v in values.values()):
                return False

            date_str = data.get("date")
            if date_str:
                try:
                    datetime.fromisoformat(date_str)
                except ValueError:
                    try:
                        datetime.strptime(date_str, "%Y-%m-%d_%H%M")
                    except ValueError:
                        return False

            return True
        except Exception:
            return False

    @staticmethod
    def _parse_date(date_str: Optional[str], fallback_timestamp: float) -> datetime:
        if date_str:
            try:
                return datetime.fromisoformat(date_str)
            except ValueError:
                try:
                    return datetime.strptime(date_str, "%Y-%m-%d_%H%M")
                except ValueError:
                    print(f"Invalid date format : {date_str}")
        return datetime.fromtimestamp(fallback_timestamp)

    def export_to_file(self, filepath: str):
        values = {
            ch.lower(): curve.values
            for ch, curve in self.curves.items()
            if any(curve.values)
        }

        output = {
            "name": self.name or "sensito",
            "color": self.color or "vrgb",
            "date": datetime.now().isoformat(timespec="minutes"),
            "values": values
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2)
