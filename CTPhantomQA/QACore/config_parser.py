import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import  Dict, Any, List, Optional

__author__ = ["Riccardo Biondi"]
__email__ = ["riccardo.biondi@proton.me"]


class PhantomConfigError(Exception):
    ...


@dataclass(frozen=True)
class HUTarget:
    r"""
    """
    angle_deg: float
    distance_mm: float
    expected_hu: float
    tolerance: float

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HUTarget":
        return cls(angle_deg=data["angle_deg"], distance_mm=data["distance_mm"], expected_hu=data["expected_hu"], tolerance=data["tolerance"])


@dataclass(frozen=True)
class ModuleConfig:
    r"""
    """
    relative_z_offset_mm: float
    targets: Dict[str, HUTarget] = field(default_factory=dict)
    extra_params: Dict[str, float] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModuleConfig":

        targets = {}
        extra_params = {key: val for key, val in data.items()  if key not in ["relative_z_offset_mm", "targets"]}

        if "targets" in data.keys():

            for key, val in data["targets"].items(): 
                targets.update({key: HUTarget.from_dict(val)})

        return cls(relative_z_offset_mm=data["relative_z_offset_mm"], targets=targets, extra_params=extra_params)


@dataclass(frozen=True)
class PhantomConfig:
    phantom_name: str
    modules: Dict[str, ModuleConfig]

    @classmethod
    def from_json(cls, path: Path | str) -> "PhantomConfig":

        with open(path, "r", encoding="utf-8") as fp:
            data = json.load(fp)

        parsed_modules = {}
        for key, val in data["modules"].items():
            parsed_modules.update({key: ModuleConfig.from_dict(val)})


        return cls(phantom_name=data["phantom_name"], modules=parsed_modules)



        