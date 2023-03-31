import json
from concurrent.futures import ThreadPoolExecutor


# ThreadPoolExecutor with 1 worker so tasks run in sequence
executor = ThreadPoolExecutor(max_workers=1)


def cache_arg(args: list):
    """ Adds caching operations to queue """
    executor.submit(_save_cache, *args)


def _save_cache(ctx, d1, d2, r1, r2, multiplier, rpm):
    """ Save to cache """

    with open("pfgun_cache.json", "r") as f:
        data = json.load(f)

        user = str(ctx.author.id)
        users = {}
        args = {"close_damage": d1, "long_damage": d2, "close_range": r1, "long_range": r2, "multiplier": multiplier, "rpm": rpm}

        # Get rid of old arguments if user already in cache
        for num, u in enumerate(data["users"]):
            if user in u:
                del data["users"][num]
                break

        # Add arguments as dict
        users[user] = args
        data["users"].append(users)

    # Save to file
    with open("pfgun_cache.json", "w") as f:
        json.dump(data, f, indent=4)


async def get_params(user) -> dict:
    """ Returns parameters of specified user from cache """

    with open("pfgun_cache.json", "r") as f:
        data = json.load(f)

        for u in data["users"]:
            if user in u:
                return u[user]


if __name__ == '__main__':
    pass    # TODO: Manual caching later uwu?
