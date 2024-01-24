"""
Custom datatypes.
"""

import dataclasses
import json
import pathlib
from typing import Any


@dataclasses.dataclass
class MacrostratObject:
    """
    Represents one object, likely a map, to import into Macrostrat.
    """

    ## Where the "original" copy of the object resides.
    origin: str
    description: dict[str, Any]

    ## Where to store a copy of the object within Macrostrat.
    scheme: str
    host: str
    bucket: str
    key: str

    ## Where to store a local copy of the object.
    local_file: pathlib.Path

    def __post_init__(self):
        """
        Convert this dataclass instance from JSON.
        """
        self.local_file = pathlib.Path(self.local_file)

    def __str__(self):
        """
        Convert this dataclass instance to JSON.
        """
        data = dataclasses.asdict(self)
        data["local_file"] = str(data["local_file"])
        return json.dumps(data)
