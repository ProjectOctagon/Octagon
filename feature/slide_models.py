from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class BoxModel:  #represents a single 'box' in the org chart.
    title: str                   # example: "Finance", "Head of COSI"
    subtitle: str                # example: "Person Name" or "NN"
    box_type: str                # example: "manager", "assistant"
    is_changed: bool = False     # for the border color of people that have changed roles


@dataclass
class SlideModel: #represents a full pptx slide.
    title: str              # example: "Mobile Networks Business Group"
    hierarchy_level: str    # example: "(N-3 unit)"
    head_of_unit: BoxModel
    type: str = "org_chart"
    assistant: Optional[BoxModel] = None
    columns: List[List[BoxModel]] = field(default_factory=list) 

@dataclass
class PresentationModel:
    slides: List[SlideModel] = field(default_factory=list)