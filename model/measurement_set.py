# model/measurement_set.py

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, List, Dict, Optional
import json



@dataclass
class ChannelCurve:
    channel: str  # "R", "G", "B", etc...
    values: List[float]  # 21 density points


@dataclass
class MeasurementSet:
    """Represents a set of measurements that can be loaded from or exported to a file.

    This class manages a measurement set including its file path, date, associated curves, optional name and color attributes.
    It provides functionalities to load measurements from a JSON file and export them back to a file.

    Attributes:
        path (Path): The path to the measurement file.
        date (datetime): The date of the measurement.
        curves (Dict[str, ChannelCurve]): Curves data keyed by channel.
        name (Optional[str]): Optional name of the measurement set.
        color (Optional[str]): Optional color information for the measurement set.
    """


    path: Path
    date: datetime
    curves: Dict[str, ChannelCurve]
    name: Optional[str] = None
    color: Optional[str] = None


    @classmethod
    def load_from_file(cls, path: Path) -> Optional["MeasurementSet"]:
        """Creates a `MeasurementSet` instance from a JSON file.

        Validates and reads the measurement data from the specified file, extracting attributes such as curves, date, name, and color.
        It parses the JSON content and instantiates a `MeasurementSet` if the file is valid and contains required data.

        Args:
            path (Path): The file path to load the measurement data from.

        Returns:
            Optional[MeasurementSet]: A `MeasurementSet` instance if successful, otherwise `None`.
        """
        try:
            data = cls._load_json_data(path)
            if data is None or not cls._is_valid_data(data):
                print(f"Invalid file ignored : {path.name}")
                return None

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
    def _load_json_data(path: Path) -> Optional[Dict[str, Any]]:
        """Loads raw JSON data from a measurement file."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data if isinstance(data, dict) else None
        except Exception:
            return None



    @classmethod
    def _is_valid_file(cls, path: Path) -> bool:
        """Validates the structure and content of a specified measurement file.

        Checks the file to ensure it contains expected JSON keys and value structures needed for a valid measurement set.
        This includes checking `values` structure and format of `date`.

        Args:
            path (Path): The file path to validate.

        Returns:
            bool: `True` if the file is considered valid, `False` otherwise.
        """
        data = cls._load_json_data(path)
        return cls._is_valid_data(data) if data is not None else False


    @staticmethod
    def _is_valid_data(data: Dict[str, Any]) -> bool:
        """Validates already loaded measurement JSON data."""
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



    @staticmethod
    def _parse_date(date_str: Optional[str], fallback_timestamp: float) -> datetime:
        """Parses a date from a given string or falls back to a timestamp.

        Attempts to parse the provided date string using standard datetime formats. 
        If parsing fails, it defaults to using the provided fallback UNIX timestamp.

        Args:
            date_str (Optional[str]): The string representation of the date.
            fallback_timestamp (float): A UNIX timestamp to fall back on if parsing the date string fails.

        Returns:
            datetime: The parsed datetime object or the datetime representation of the fallback timestamp.
        """
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
        """Exports the `MeasurementSet` data to a JSON file at the specified path.

        Converts the current `MeasurementSet` instance into a JSON structure and writes it to the specified file, 
        including its name, color, date, and curves data.

        Args:
            filepath (str): The path where the measurement data should be exported.
        """
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
