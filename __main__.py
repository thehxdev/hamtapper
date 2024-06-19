import time
import httpx
import asyncio
import random as rand
from threading import Thread

# Local
from users import USERS


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
                       headers=self.rheaders)

        jdata = r.json()
        if r.status_code != 200:
            print(f"[ERROR] user \"{self.name}\": server returned {r.status_code} code")
            print(f"[ERROR] {jdata}")
            return None

        return jdata


    async def tapCycle(self) -> None:
        deepSleepSec: int = (self.initialAvailableTaps // 3) + rand.randint(100, 300)
        self.availableTaps = await self._getCurrentAvailableTaps()

        while True:
            while True:
                tapCount = rand.randint(25, 50)
                jdata = await self.tap(tapCount)
                if jdata is None:
                    return

                self.availableTaps = jdata["clickerUser"]["availableTaps"]
                print(f"[INFO] user \"{self.name}\" balance: ", round(jdata["clickerUser"]["balanceCoins"], 2))

                if self.availableTaps <= 20:
                    break
                await asyncio.sleep(rand.randint(5, 15))

            print(f"[INFO] user \"{self.name}\" deep sleep ({deepSleepSec} sec)")
            await asyncio.sleep(deepSleepSec)

    
    def buyUpgrade(self, upgradeId: str) -> None:
        rdata = {
            "upgradeId": upgradeId,
            "timestamp": int(time.time()),
        }

        r = httpx.post("https://api.hamsterkombat.io/clicker/buy-upgrade",
                       json=rdata,
                       headers=self.rheaders)

        jdata: dict = r.json()
        if r.status_code != 200:
            print(f"[ERROR] user \"{self.name}\": server returned {r.status_code} code")
            print(jdata)
            return


    async def _getCurrentAvailableTaps(self) -> int:
        jdata = await self.tap(1)
        if jdata is None:
            return -1
        return int(jdata["clickerUser"]["availableTaps"])



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



def main() -> None:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    Thread(target=loop.run_forever, daemon=False).start()

    users = USERS

    # userThreads: list[Thread] = []
    for user in users:
        # userThreads.append(runUserMultiThread(user["name"],
        #                                       user["auth"],
        #                                       user["tapCost"],
        #                                       user["initialAvailableTaps"]))
        runUserSingleThread(user["name"],
                            user["auth"],
                            user["tapCost"],
                            user["initialAvailableTaps"],
                            loop)


if __name__ == "__main__":
    main()
