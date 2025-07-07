from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import json


@dataclass
class ChannelCurve:
    channel: str  # "R", "G", "B", etc.
    values: List[float]  # 21 points de densité


@dataclass
class MeasurementSet:
    path: Path
    date: datetime  # date
    curves: Dict[str, ChannelCurve]  # values for each channel
    name: Optional[str] = None       # name
    color: Optional[str] = None      # color channel(rgb, cmy)
    json_date: Optional[str] = None  # date


    @classmethod
    def load_from_file(cls, path: Path) -> Optional["MeasurementSet"]:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            name = data.get("name")
            color = data.get("color")
            json_date = data.get("date")

            values_dict = data.get("values", {})
            curves = {}
            for channel, values in values_dict.items():
                if isinstance(values, list) and len(values) == 21:
                    curves[channel.upper()] = ChannelCurve(channel=channel.upper(), values=values)

            if not curves:
                print(f"no curve found in: {values_dict.items()}")
                return None

            stat = path.stat()
            return cls(
                path=path,
                name=name,
                color=color,
                json_date=json_date,
                date=datetime.fromtimestamp(stat.st_mtime),
                curves=curves
            )
        except (json.JSONDecodeError, OSError, ValueError) as e:
            print(f"Erreur lors du chargement de {path} : {e}")
            return None


    def export_to_file(self, filepath: str):
        """
        Export current measurement to JSON file using internal structure.
        """
        values = {
            ch.lower(): curve.values
            for ch, curve in self.curves.items()
            if any(curve.values)
        }

        output = {
            "name": self.name or "sensito",
            "color": self.color or "vrgb",
            "date": datetime.now().strftime("%Y-%m-%d_%H%M"),
            "values": values
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2)
