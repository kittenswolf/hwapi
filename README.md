# hwapi: Happy Wheels API Wrapper


### Installation

Requirement: Python3.6+

```
pip(3) install git+https://github.com/kittenswolf/hwapi.git
pip(3) install -r requirements.txt
```

### Usage (async)

```python
import asyncio
import hwapi

client = hwapi.client(useragent="test")

async def test():
    jim = await client.user(2)
    async for level in jim.levels("newest", "anytime"):
        print("Replays for Jim's level '{}':".format(level.name))
        async for replay in level.replays("completion_time"):
            print("    ID: {} - time: {}".format(replay.id, replay.completion_time))

    featured_levels = await client.featured_levels()
    print("There are {} featured levels.".format(len(featured_levels)))

    async for level in client.levels("newest", "anytime"):
        user_location = await level.author.location()
        user_joined = await level.author.date_joined()
        print("{}'s author: {} location: {}, date joined: {}".format(level.name, level.author.name, user_location, user_joined))


loop = asyncio.get_event_loop()
loop.run_until_complete(test())
```



