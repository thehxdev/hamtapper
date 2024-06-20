import sys
import asyncio
import hamtapper as ht
from users import USERS


def findUser(users: list, name: str) -> dict | None:
    for i in range(len(users)):
        if name == users[i]["name"]:
            return users[i]
    return None


async def main() -> None:
    argv = sys.argv
    u = findUser(USERS, argv[1])
    if u is None:
        print(f"[ERROR] user \"{argv[1]}\" not found. Press (Ctrl+C) to exit...")
        exit(1)

    user = ht.ClickerUser(u["name"], u["auth"], u["tapCost"], u["initialAvailableTaps"])
    await user._setUserInfo()

    max_budget = int(input("Enter Max budget: "))
    maxProfit, selectedUpgrades = await user.calcBestUpgrades(max_budget)

    try:
        print(f"User name: {user.name}")
        print(f"Max profit with budget {max_budget}: {maxProfit}")
        _ = input("Do you want to continue? (Ctrl+C to exit)")
    except KeyboardInterrupt:
        exit(0)

    for upgrade in selectedUpgrades:
        # print(f"ID: {upgrade['id']}\t\tPrice: {upgrade['price']}\t\tProfit: {upgrade['profitPerHourDelta']}")
        user.buyUpgrade(upgrade["id"])
        await asyncio.sleep(2)


if __name__ == "__main__":
    asyncio.run(main())
