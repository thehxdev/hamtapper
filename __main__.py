import asyncio
from threading import Thread
import hamtapper as ht
from users import USERS


def main() -> None:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    Thread(target=loop.run_forever, daemon=False).start()

    users = USERS

    # userThreads: list[Thread] = []
    for user in users:
        # userThreads.append(ht.runUserMultiThread(user["name"],
        #                                          user["auth"],
        #                                          user["tapCost"],
        #                                          user["initialAvailableTaps"]))
        ht.runUserSingleThread(user["name"],
                               user["auth"],
                               user["tapCost"],
                               user["initialAvailableTaps"],
                               loop)


if __name__ == "__main__":
    main()
