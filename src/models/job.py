from dataclasses import dataclass


@dataclass
class JobRecord:
    title: str
    company: str
    description: str
    location: str
    url: str
    experience: str