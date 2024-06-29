import time
import httpx
import asyncio
import random as rand
from threading import Thread
from heapq import heappush, heappop



## For calculating upgrades
class Node:
    def __init__(self, level, profit, weight, bound, selected):
        self.level = level
        self.profit = profit
        self.weight = weight
        self.bound = bound
        self.selected = selected

    def __lt__(self, other):
        return self.bound > other.bound


class ClickerUser:
    def __init__(self,
                 name: str,
                 authKey: str,
                 tapCost: int,
                 initialAvailableTaps: int) -> None:
        self.name = name
        self.tapCost = tapCost
        self.initialAvailableTaps = initialAvailableTaps
        self.availableTaps = initialAvailableTaps
        self.balance = 0

        self.rheaders = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:126.0) Gecko/20100101 Firefox/126.0",
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.5",
            # "Accept-Encoding": "gzip, deflate, br, zstd",
            "Referer": "https://hamsterkombat.io/",
            "Authorization": f"{authKey}",
            "Content-Type": "application/json",
            "Origin": "https://hamsterkombat.io",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "Priority": "u=4",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
        }


    async def tap(self, tapCount: int) -> dict | None:
        rdata = {
            "count": tapCount,
            "availableTaps": self.availableTaps,
            "timestamp": int(time.time()),
        }

        r = httpx.post("https://api.hamsterkombat.io/clicker/tap",
                       json=rdata,
                       headers=self.rheaders,
                       timeout=10)

        jdata = r.json()
        if r.status_code != 200:
            print(f"[ERROR] user \"{self.name}\": server returned {r.status_code} code")
            print(f"[ERROR] {jdata}")
            return None

        return jdata


    async def tapCycle(self) -> None:
        deepSleepSec: int = (self.initialAvailableTaps // 3) + rand.randint(100, 300)
        await self._setUserInfo()
        if self.availableTaps == -1:
            return

        while True:
            while True:
                tapCount = rand.randint(25, 50)
                jdata = await self.tap(tapCount)
                if jdata is None:
                    return

                self.availableTaps = jdata["clickerUser"]["availableTaps"]
                self.balance = round(jdata["clickerUser"]["balanceCoins"], 2)
                print(f"[INFO] user \"{self.name}\" balance: ", self.balance)

                if self.availableTaps <= 20:
                    break
                await asyncio.sleep(rand.randint(5, 15))

            print(f"[INFO] user \"{self.name}\" deep sleep ({deepSleepSec} sec)")
            await asyncio.sleep(deepSleepSec)

    
    async def calcBestUpgrades(self, max_budget: int) -> tuple[int, list]:
        async def getUpgradesInfo() -> dict | None:
            r = httpx.post("https://api.hamsterkombat.io/clicker/upgrades-for-buy",
                           headers=self.rheaders,
                           timeout=10)

            jdata = r.json()
            if r.status_code != 200:
                print(f"[ERROR] user \"{self.name}\": server returned {r.status_code} code")
                print(f"[ERROR] {jdata}")
                return None

            return jdata

        def calculate_bound(node, n, max_budget, upgrades):
            if node.weight >= max_budget:
                return 0

            profit_bound = node.profit
            j = node.level + 1
            total_weight = node.weight

            while j < n and total_weight + upgrades[j]["price"] <= max_budget:
                total_weight += upgrades[j]["price"]
                profit_bound += upgrades[j]["profitPerHourDelta"]
                j += 1

            if j < n and upgrades[j]["price"] != 0:
                profit_bound += (max_budget - total_weight) * upgrades[j]["profitPerHourDelta"] / upgrades[j]["price"]

            return profit_bound

        def knapsack(upgrades, max_budget):
            upgrades = [u for u in upgrades if u["price"] != 0]
            upgrades.sort(key=lambda x: x["profitPerHourDelta"] / x["price"], reverse=True)
            n = len(upgrades)

            pq = []
            v = Node(-1, 0, 0, 0.0, [])
            max_profit = 0
            selected_upgrades = []
            heappush(pq, v)

            while pq:
                v = heappop(pq)

                if v.level == -1:
                    u_level = 0
                elif v.level == n - 1:
                    continue
                else:
                    u_level = v.level + 1

                if u_level < n:
                    u = Node(u_level, v.profit + upgrades[u_level]["profitPerHourDelta"], v.weight + upgrades[u_level]["price"], 0.0, v.selected + [upgrades[u_level]])
                    u.bound = calculate_bound(u, n, max_budget, upgrades)

                    if u.weight <= max_budget and u.profit > max_profit:
                        max_profit = u.profit
                        selected_upgrades = u.selected

                    if u.bound > max_profit:
                        heappush(pq, u)

                if u_level < n:
                    u = Node(u_level, v.profit, v.weight, 0.0, v.selected)
                    u.bound = calculate_bound(u, n, max_budget, upgrades)

                    if u.bound > max_profit:
                        heappush(pq, u)

            return max_profit, selected_upgrades

        data = await getUpgradesInfo()
        if data is None:
            return 0, []

        upgrades = [
            item for item in data["upgradesForBuy"]
            if not item["isExpired"] and item["isAvailable"]
        ]

        return knapsack(upgrades, max_budget)


    def buyUpgrade(self, upgradeId: str) -> None:
        rdata = {
            "upgradeId": upgradeId,
            "timestamp": int(time.time()),
        }

        r = httpx.post("https://api.hamsterkombat.io/clicker/buy-upgrade",
                       json=rdata,
                       headers=self.rheaders,
                       timeout=10)

        jdata: dict = r.json()
        if r.status_code != 200:
            print(f"[ERROR] user \"{self.name}\": server returned {r.status_code} code")
            print(jdata)
            return
        print(f"[INFO] upgrade with id \"{upgradeId}\" bought for user \"{self.name}\"")


    async def _getUserInfo(self) -> dict | None:
        jdata = await self.tap(1)
        return jdata


    async def _setUserInfo(self) -> None:
        jdata = await self._getUserInfo()
        if jdata is None:
            return

        u = jdata["clickerUser"]
        self.availableTaps = u["availableTaps"]
        self.balance = u["balanceCoins"]



def runUserSingleThread(name: str,
                        auth: str,
                        tapCost: int,
                        initialAvailableTaps: int,
                        loop: asyncio.AbstractEventLoop) -> None:
    u = ClickerUser(name, auth, tapCost, initialAvailableTaps)
    asyncio.run_coroutine_threadsafe(u.tapCycle(), loop)


def runUserMultiThread(name: str,
                       auth: str,
                       tapCost: int,
                       initialAvailableTaps: int) -> Thread:
    u = ClickerUser(name, auth, tapCost, initialAvailableTaps)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    t = Thread(target=loop.run_forever, daemon=False)
    t.start()

    asyncio.run_coroutine_threadsafe(u.tapCycle(), loop)
    return t
