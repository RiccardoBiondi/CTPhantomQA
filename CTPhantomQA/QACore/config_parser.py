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

    name: str
    analysis_type: str
    relative_z_offset_mm: float
    parameters: Dict[str, Any]


    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModuleConfig":

        return cls(name=data["name"], analysis_type=data["analysis_type"], relative_z_offset_mm=data["relative_z_offset_mm"], parameters=data["parameters"])


@dataclass(frozen=True)
class PhantomConfig:
    phantom_name: str
    modules: List[ModuleConfig]

    @classmethod
    def from_json(cls, path: Path | str) -> "PhantomConfig":

        with open(path, "r", encoding="utf-8") as fp:
            data = json.load(fp)

        parsed_modules = []
        for module in data["modules"]:
            parsed_modules.append(ModuleConfig.from_dict(module)) 


        return cls(phantom_name=data["phantom_name"], modules=parsed_modules)



        