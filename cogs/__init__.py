from .crime import CrimeCommands
from .economy import EconomyCommands
from .expeditions import ExpeditionCommands
from .games import GameCommands
from .inventory import InventoryCommands
from .profile import ProfileCommands
from .rewards import RewardCommands
from .shop import ShopCommands
from .study import StudyCommands
from .work import WorkCommands


async def add_core_cogs(bot):
    await bot.add_cog(EconomyCommands(bot))
    await bot.add_cog(InventoryCommands(bot))
    await bot.add_cog(RewardCommands(bot))
    await bot.add_cog(CrimeCommands(bot))
    await bot.add_cog(StudyCommands(bot))
    await bot.add_cog(GameCommands(bot))
    await bot.add_cog(ProfileCommands(bot))
    await bot.add_cog(WorkCommands(bot))
    await bot.add_cog(ExpeditionCommands(bot))
    await bot.add_cog(ShopCommands(bot))


__all__ = [
    "add_core_cogs",
    "CrimeCommands",
    "EconomyCommands",
    "ExpeditionCommands",
    "GameCommands",
    "InventoryCommands",
    "ProfileCommands",
    "RewardCommands",
    "ShopCommands",
    "StudyCommands",
    "WorkCommands",
]
