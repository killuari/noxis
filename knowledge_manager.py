import aiosqlite, json
from user_manager import *

class KnowledgeManager:
    KNOWLEDGE_THRESHOLDS = {
    "beginner": 0,
    "novice": 50,
    "intermediate": 250,
    "advanced": 750,
    "expert": 2000,
    "master": 5000
    }

    @staticmethod
    async def get_knowledge_threshold(points: int):
        for threshold in reversed(KnowledgeManager.KNOWLEDGE_THRESHOLDS):
            if points >= KnowledgeManager.KNOWLEDGE_THRESHOLDS[threshold]:
                return threshold
        
        return "beginner"

    @staticmethod
    async def add_knowledge(user_id: int, science: int = 0, medicine: int = 0, economics: int = 0, literature: int = 0, knowledge: dict = None):
        if not await UserManager.user_exists(user_id):
            print("User doesnt exist")
            return
        
        async with aiosqlite.connect("database.db") as db:
            cursor = await db.cursor()
            current_knowledge = await KnowledgeManager.get_knowledge(user_id)
            if not knowledge:
                knowledge = {"science": science, "medicine": medicine, "economics": economics, "literature": literature}
            
            new_knowledge = {i: current_knowledge[i] + knowledge[i] for i in current_knowledge} # sehr geile dict comprehension wow
            await cursor.execute("UPDATE users SET knowledge=? WHERE user_id=?", (json.dumps(new_knowledge), user_id))
            await db.commit()

    @staticmethod
    async def get_knowledge(user_id: int) -> dict:
        knowledge = {}
        if not await UserManager.user_exists(user_id):
            print("User doesnt exist")
            return knowledge
        
        async with aiosqlite.connect("database.db") as db:
            cursor = await db.cursor()
            await cursor.execute("SELECT knowledge FROM users WHERE user_id=?", (user_id,))
            result = await cursor.fetchone()
            if result:
                knowledge = json.loads(result[0])

        return knowledge

    @staticmethod
    async def has_knowledge_requirements_int(user_id: int, requirements: dict) -> bool:
        if not await UserManager.user_exists(user_id):
            print("User doesnt exist")
            return False
        
        knowledge = await KnowledgeManager.get_knowledge(user_id)
        return not False in [knowledge[i] >= requirements[i] for i in requirements] # ich liebe den one liner
    
    @staticmethod
    async def has_knowledge_requirements_str(user_id: int, requirements: dict) -> bool:
        if not await UserManager.user_exists(user_id):
            print("User doesnt exist")
            return False

        int_requirements = {category: KnowledgeManager.KNOWLEDGE_THRESHOLDS[requirements[category]] for category in requirements}
        return await KnowledgeManager.has_knowledge_requirements_int(user_id, int_requirements)
