from typing import List

from models.job import Job


JOBS = {
    # Low tier jobs
    1: Job(
        id=1,
        name="Cleaner",
        salary=500,
        cooldown=5,
        required_level=1,
        required_knowledge={"science": 0, "economics": 0, "literature": 0, "medicine": 0}
    ),
    2: Job(
        id=2,
        name="Cashier",
        salary=650,
        cooldown=5,
        required_level=1,
        required_knowledge={"science": 0, "economics": 50, "literature": 0, "medicine": 0}
    ),
    3: Job(
        id=3,
        name="Warehouse Worker",
        salary=800,
        cooldown=5,
        required_level=1,
        required_knowledge={"science": 0, "economics": 250, "literature": 0, "medicine": 0}
    ),
    4: Job(
        id=4,
        name="Head Chef",
        salary=1000,
        cooldown=5,
        required_level=1,
        required_knowledge={"science": 50, "economics": 50, "literature": 50, "medicine": 100}
    ),
    
    # Mid tier Jobs
    5: Job(
        id=5,
        name="Elementary School Teacher",
        salary=1500,
        cooldown=30,
        required_level=5,
        required_knowledge={"science": 0, "economics": 0, "literature": 750, "medicine": 0}  
    ),
    6: Job(
        id=6,
        name="Electrician ",
        salary=1750,
        cooldown=30,
        required_level=5,
        required_knowledge={"science": 750, "economics": 0, "literature": 0, "medicine": 0}
    ),
    7: Job(
        id=7,
        name="Police Officer",
        salary=2000,
        cooldown=30,
        required_level=5,
        required_knowledge={"science": 0, "economics": 750, "literature": 0, "medicine": 0}
    ),
    8: Job(
        id=8,
        name="Nurse",
        salary=2250,
        cooldown=30,
        required_level=5,
        required_knowledge={"science": 0, "economics": 0, "literature": 0, "medicine": 750}
    ),
    
    # High tier jobs
    9: Job(
        id=9,
        name="Archeologist",
        salary=3500,
        cooldown=60,
        required_level=15,
        required_knowledge={"science": 0, "economics": 0, "literature": 2000, "medicine": 0}
    ),
    10: Job(
        id=10,
        name="Lawyer",
        salary=4000,
        cooldown=60,
        required_level=15,
        required_knowledge={"science": 0, "economics": 2000, "literature": 0, "medicine": 0}    
    ),
    11: Job(
        id=11,
        name="Doctor",
        salary=4500,
        cooldown=60,
        required_level=15,
        required_knowledge={"science": 0, "economics": 0, "literature": 0, "medicine": 2000}        
    ),
    12: Job(
        id=12,
        name="Senior Software Developer",
        salary=5000,
        cooldown=60,
        required_level=15,
        required_knowledge={"science": 2000, "economics": 0, "literature": 0, "medicine": 0}        
    )
}


class JobManager:
    @staticmethod
    async def get_all_jobs() -> List[Job]:
        """Holt alle verfügbaren jobs"""        
        return list(JOBS.values())
    
    @staticmethod
    async def get_job(job_id: int) -> Job | None:
        return JOBS.get(job_id) if job_id not in range(1, len(JOBS) + 1) else None
