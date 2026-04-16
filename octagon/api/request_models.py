from dataclasses import dataclass
from typing import Optional



class GenerateRequestPpt:
    org_id: str
    include_externals: bool = False
    include_trainees: bool = False
    template_name: str = "default"
    output_name: Optional[str] = None
    
