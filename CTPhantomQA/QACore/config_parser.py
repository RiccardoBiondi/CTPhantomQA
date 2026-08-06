import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import  Dict, Any, List, Optional

__author__ = ["Riccardo Biondi"]
__email__ = ["riccardo.biondi@proton.me"]


class PhantomConfigError(Exception):
    ...



@dataclass(frozen=True)
class ModuleConfig:
    r"""
    """
    relative_z_offset_mm: float
    analyses: Dict[str, Dict[str, Any]]


    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModuleConfig":

        return cls(relative_z_offset_mm=data["relative_z_offset_mm"],analyses=data["analyses"])


@dataclass(frozen=True)
class PhantomConfig:
    phantom_name: str
    modules: Dict[str, ModuleConfig]

    @classmethod
    def from_json(cls, path: Path | str) -> "PhantomConfig":

        with open(path, "r", encoding="utf-8") as fp:
            data = json.load(fp)

        #TODO add sanity checks!
        parsed_modules = {key: ModuleConfig.from_dict(val) for key, val in data["modules"].items()}


        return cls(phantom_name=data["phantom_name"], modules=parsed_modules)



        