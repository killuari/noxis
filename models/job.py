from dataclasses import dataclass


@dataclass
class Job:
    id: int 
    name: str 
    salary: int 
    cooldown: int
    required_level: int  
    required_knowledge: dict 
