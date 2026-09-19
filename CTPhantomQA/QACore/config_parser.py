import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import  Dict, Any, List, Optional, NoReturn

from .roi import BaseROI

__author__ = ["Riccardo Biondi"]
__email__ = ["riccardo.biondi@proton.me"]


def _dict_sanity_check(data: Dict[str, Any], must_contain_keys: List[str]) -> NoReturn:
    return 

class PhantomConfigError(Exception):
    ...


class ROIConfigFactory:

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BaseROI":

        # TODO substitute with a call to the ROI register
        if data["shape"] == "circular": 
            from .roi import CirleROI
            
            return CirleROI.from_dict(data)
        elif data["shape"] == "sphere": 
            from .roi import SphereROI
            return SphereROI.from_dict(data)
        



@dataclass(frozen=True)
class ModuleConfig:
    r"""
    """
    module_name: str
    relative_z_offset_mm: float
    rois: List[BaseROI]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModuleConfig":

        _dict_sanity_check(data=data, must_contain_keys=["module_name", "relative_z_offset_mm", "rois"])

        return cls(module_name=data["module_name"], relative_z_offset_mm= data["relative_z_offset_mm"], rois=[ROIConfigFactory.from_dict(roi) for roi in data["rois"]])
        
        #cls(module_name="test_module", relative_z_offset_mm=.5, rois=[ROIConfigFactory.from_dict({"shape": None})])


@dataclass(frozen=True)
class PhantomConfig:
    protocol_name: str
    phantom_name: str
    modules: List[ModuleConfig]

    @classmethod
    def from_json(cls, path: Path | str) -> "PhantomConfig":
        r"""
        """
        with open(path, "r", encoding="utf-8") as fp:
            data = json.load(fp)

        _ = _dict_sanity_check(data=data, must_contain_keys=["protocol_name", "phantom_name", "modules"])

        return cls(protocol_name=data["protocol_name"], phantom_name=data["phantom_name"], modules=[ModuleConfig.from_dict(mod) for mod in data["modules"]])
        #cls(protocol_name="test", phantom_name="test", modules=[ModuleConfig.from_dict({})])



#@dataclass(frozen=True)
#class PhantomConfig:
#    phantom_name: str
#    modules: Dict[str, ModuleConfig]
#
#    @classmethod
#    def from_json(cls, path: Path | str) -> "PhantomConfig":
#
#        with open(path, "r", encoding="utf-8") as fp:
#            data = json.load(fp)
#
#        #TODO add sanity checks!
#        parsed_modules = {key: ModuleConfig.from_dict(val) for key, val in data["modules"].items()}
#
#
#        return cls(phantom_name=data["phantom_name"], modules=parsed_modules)



        