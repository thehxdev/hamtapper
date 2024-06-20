import asyncio
import hamtapper as ht
from users import USERS


async def main() -> None:
    u = USERS[0]
    user = ht.ClickerUser(u["name"], u["auth"], u["tapCost"], u["initialAvailableTaps"])
    await user._setUserInfo()
    _, selectedUpgrades = await user.calcBestUpgrades()
    for upgrade in selectedUpgrades:
        # print(f"ID: {upgrade['id']}\t\tPrice: {upgrade['price']}\t\tProfit: {upgrade['profitPerHourDelta']}")
        user.buyUpgrade(upgrade["id"])
        await asyncio.sleep(2)


if __name__ == "__main__":
    asyncio.run(main())
