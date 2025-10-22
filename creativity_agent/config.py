from pydantic import BaseModel
from pathlib import Path
import json
from typing import Dict, List, Optional

class ModelConfig(BaseModel):
    model_id: str
    high_temp: float
    low_temp: float
    streaming: bool = True  # Default to True for backward compatibility

class StepConfig(BaseModel):
    id: str
    model: str
    temperature: str  # "high" or "low"
    prompt_file: str
    next: Optional[str] = None

class JudgeConfig(BaseModel):
    model_id: str
    temperature: float
    timeout: int
    streaming: bool = True  # Default to True for backward compatibility

class ChaosGeneratorConfig(BaseModel):
    model_id: str
    temperature: float
    max_web_searches: int
    timeout_per_seed: int
    streaming: bool = True  # Default to True for backward compatibility

class FlowConfig(BaseModel):
    iterations: int
    models: Dict[str, ModelConfig]
    steps: List[StepConfig]
    loop_back_to: Optional[str] = None
    final_step: str
    judge: JudgeConfig
    chaos_generator: ChaosGeneratorConfig
    
    @classmethod
    def from_json(cls, json_path: Path) -> 'FlowConfig':
        with open(json_path, 'r') as f:
            data = json.load(f)
        return cls(**data)
    
    def get_prompt_path(self, step_id: str) -> Path:
        step = next(s for s in self.steps if s.id == step_id)
        return Path(__file__).parent / "prompts" / step.prompt_file
    
    def load_prompt(self, step_id: str) -> str:
        path = self.get_prompt_path(step_id)
        if path.exists():
            return path.read_text()
        else:
            return f"Default prompt for {step_id}"