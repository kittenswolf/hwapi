# -*- coding: utf-8 -*-

import time
import xml
import asyncio

import aiohttp
import xmltodict
from bs4 import BeautifulSoup
import cachetools

from . import models


class client:

    def __init__(self, *, useragent, timeout=5, delay=1, max_tries=5, user_cache_maxsize=300, user_cache_ttl=60):
        self.SORTED_BY_POSS = ["newest", "oldest", "plays", "rating"]
        self.UPLOADED_BY_POSS = ["today", "week", "month", "anytime"]
        self.REPLAY_SORTED_BY_POSS = ["completion_time", "newest", "oldest", "rating"]

        self.useragent = useragent
        self.timeout = timeout
        self.delay = delay
        self.max_tries = max_tries

        self._last_request = 0
        self._user_cache = cachetools.TTLCache(maxsize=user_cache_maxsize, ttl=user_cache_ttl)
        self._featured_cache = []

    async def _ensure_delay(self):
        if time.time() - self._last_request < self.delay:
            await asyncio.sleep(self.delay - (time.time() - self._last_request))

    async def _fetch_post(self, url, payload):
        await self._ensure_delay()

        tries = 0
        while tries < self.max_tries:
            try:
                async with aiohttp.ClientSession(headers={'User-Agent': self.useragent}) as session:
                    async with session.post(url, data=payload, timeout=self.timeout) as resp:
                        self._last_request = time.time()
                        return await resp.text()
            except asyncio.TimeoutError:
                tries += 1

            if self.delay > 0:
                await asyncio.sleep(self.delay * tries)
            else:
                await asyncio.sleep(1.5 * tries)

    async def _fetch_get(self, url):
        await self._ensure_delay()

        tries = 0
        while tries < self.max_tries:
            try:
                async with aiohttp.ClientSession(headers={'User-Agent': self.useragent}) as session:
                    async with session.get(url, timeout=self.timeout) as resp:
                        self._last_request = time.time()
                        return await resp.text()
            except asyncio.TimeoutError:
                tries += 1

            if self.delay > 0:
                await asyncio.sleep(self.delay * tries)
            else:
                await asyncio.sleep(1.5 * tries)

    async def level(self, level_id: int):
        await self._ensure_featured_cache()

        payload = {
            'action': 'get_level',
            'level_id': level_id
        }

        raw_metadata = await self._fetch_post("https://totaljerkface.com/get_level.hw", payload)
        metadata_dict = xmltodict.parse(raw_metadata)

        return models.Level(
            data=metadata_dict["lvs"]["lv"],
            state=self
        )

    async def replay(self, replay_id: int):
        payload = {
            'action': 'get_combined',
            'replay_id': replay_id
        }

        raw_metadata = await self._fetch_post("https://totaljerkface.com/replay.hw", payload)
        metadata_dict = xmltodict.parse(raw_metadata)

        return models.Replay(
            data=metadata_dict["combined_data"],
            state=self
        )

    async def fetch_user(self, user_id: int):
        return await self.user(user_id, force=True)

    async def user(self, user_id: int, fetch=False):
        if not fetch:
            if user_id in self._user_cache:
                return self._user_cache[user_id]

        user_page_html = await self._fetch_get("https://totaljerkface.com/profile.tjf?uid={}".format(user_id))
        soup = BeautifulSoup(user_page_html, "lxml")

        if soup.find("div", class_="header").text == "This user's account is not active.":
            user_data = {"active": False}
        else:
            user_data = {"active": True}

            # Construct user_data
            profile_table = soup.find("table", class_="profile_table")
            mapped_profile_table = {}

            for row in profile_table.find_all("tr"):
                columns = row.find_all("td")
                mapped_profile_table[columns[0].text.replace(":", "").lower()] = columns[1].text.strip()

            name = soup.find("div", class_="header").text.split("'s Profile")[0]

            user_data["profile_table"] = mapped_profile_table
            user_data["name"] = name
            user_data["id"] = user_id

        user = models.User(
            data=user_data,
            state=self
        )

        self._user_cache[user_id] = user
        return user

    async def user_levels(self, user_id: int, sorted_by, uploaded, page=1, single=True):
        if not sorted_by in self.SORTED_BY_POSS:
            raise ValueError("invalid parameter for sorted_by: {}".format(sorted_by))

        if not uploaded in self.UPLOADED_BY_POSS:
            raise ValueError("invalid parameter for uploaded: {}".format(uploaded))

        await self._ensure_featured_cache()

        exhausted = False
        previous_batch = []
        while not exhausted:
            payload = {
                'page': page,
                'user_id': user_id,
                'action': 'get_pub_by_user',
                'uploaded': uploaded,
                'sortby': sorted_by
            }

            raw_metadata = await self._fetch_post("https://totaljerkface.com/get_level.hw", payload)

            try:
                metadata_dict = xmltodict.parse(raw_metadata)
            except xml.parsers.expat.ExpatError:
                return
                yield

            if metadata_dict["lvs"]:
                if type(metadata_dict["lvs"]["lv"]) == list:
                    output = []
                    for level in metadata_dict["lvs"]["lv"]:
                        parsed_level = models.Level(
                            state=self,
                            data=level
                        )
                        output.append(parsed_level)

                    if output == previous_batch:
                        exhausted = True
                    else:
                        previous_batch = output
                        for level in output:
                            yield level
                else:
                    exhausted = True
                    yield models.Level(state=self, data=metadata_dict["lvs"]["lv"])
            else:
                exhausted = True

            if single:
                exhausted = True
            else:
                page += 1

    async def levels(self, sorted_by, uploaded, page=1, single=False):
        if not sorted_by in self.SORTED_BY_POSS:
            raise ValueError("invalid parameter for sorted_by: {}".format(sorted_by))

        if not uploaded in self.UPLOADED_BY_POSS:
            raise ValueError("invalid parameter for uploaded: {}".format(uploaded))

        await self._ensure_featured_cache()

        exhausted = False
        previous_batch = []
        while not exhausted:
            payload = {
                'action': 'get_all',
                'uploaded': uploaded,
                'sortby': sorted_by,
                'page': page
            }

            raw_metadata = await self._fetch_post("https://totaljerkface.com/get_level.hw", payload)

            try:
                metadata_dict = xmltodict.parse(raw_metadata)
            except xml.parsers.expat.ExpatError:
                return
                yield

            if type(metadata_dict["lvs"]["lv"]) == list:
                output = []
                for level in metadata_dict["lvs"]["lv"]:
                    parsed_level = models.Level(
                        state=self,
                        data=level
                    )
                    output.append(parsed_level)

                if output == previous_batch:
                    exhausted = True
                else:
                    previous_batch = output
                    for level in output:
                        yield level
            else:
                exhausted = True
                yield models.Level(state=self, data=metadata_dict["lvs"]["lv"])

            if single:
                exhausted = True
            else:
                page += 1

    async def level_replays(self, level_id: int, sorted_by, page=1, single=False):
        if not sorted_by in self.REPLAY_SORTED_BY_POSS:
            raise ValueError("invalid parameter for sorted_by: {}".format(sorted_by))

        exhausted = False
        previous_batch = []
        while not exhausted:
            payload = {
                'action': 'get_all_by_level',
                'level_id': level_id,
                'page': page,
                'sortby': sorted_by
            }

            raw_metadata = await self._fetch_post("https://totaljerkface.com/replay.hw", payload)

            try:
                metadata_dict = xmltodict.parse(raw_metadata)
            except xml.parsers.expat.ExpatError:
                return
                yield

            if "rp" in metadata_dict["rps"]:
                if type(metadata_dict["rps"]["rp"]) == list:
                    output = []
                    for level in metadata_dict["rps"]["rp"]:
                        parsed_replay = models.Replay(
                            state=self,
                            data=level
                        )
                        output.append(parsed_replay)

                    if output == previous_batch:
                        exhausted = True
                    else:
                        previous_batch = output
                        for replay in output:
                            yield replay
                else:
                    exhausted = True
                    yield models.Replay(state=self, data=metadata_dict["rps"]["rp"])
            else:
                exhausted = True

            if single:
                exhausted = True
            else:
                page += 1

    async def featured_levels(self, fetch=True):
        if len(self._featured_cache) > 0:
            return self._featured_cache
        else:
            payload = {'action': 'get_featured'}

            raw_metadata = await self._fetch_post("https://totaljerkface.com/get_level.hw", payload)
            metadata_dict = xmltodict.parse(raw_metadata)

            featured_levels = []
            for level in metadata_dict["lvs"]["lv"]:
                level["featured"] = True
                parsed_level = models.Level(
                    state=self,
                    data=level
                )
                featured_levels.append(parsed_level)

            self._featured_cache = featured_levels
            return featured_levels

    async def fetch_featured_levels(self):
        return await self.featured_levels(fetch=True)

    async def _ensure_featured_cache(self):
        if not len(self._featured_cache) > 0:
            await self.featured_levels()

    async def _search(self, search_by, term, sorted_by, uploaded, page=1, single=False):
        if not sorted_by in self.SORTED_BY_POSS:
            raise ValueError("invalid parameter for sorted_by: {}".format(sorted_by))

        if not uploaded in self.UPLOADED_BY_POSS:
            raise ValueError("invalid parameter for uploaded: {}".format(uploaded))

        await self._ensure_featured_cache()

        exhausted = False
        previous_batch = []
        while not exhausted:
            payload = {
                'page': page,
                'uploaded': uploaded,
                'sterm': term,
                'action': 'search_by_{}'.format(search_by),
                'sortby': sorted_by
            }

            raw_metadata = await self._fetch_post("https://totaljerkface.com/get_level.hw", payload)

            try:
                metadata_dict = xmltodict.parse(raw_metadata)
            except xml.parsers.expat.ExpatError:
                return
                yield

            if "lv" in metadata_dict["lvs"]:
                if type(metadata_dict["lvs"]["lv"]) == list:
                    output = []
                    for level in metadata_dict["lvs"]["lv"]:
                        parsed_level = models.Level(
                            state=self,
                            data=level
                        )
                        output.append(parsed_level)

                    if output == previous_batch:
                        exhausted = True
                    else:
                        previous_batch = output
                        for level in output:
                            yield level
                else:
                    exhausted = True
                    yield models.Level(state=self, data=metadata_dict["lvs"]["lv"])
            else:
                exhausted = True

            if single:
                exhausted = True
            else:
                page += 1

    def search_by_level(self, *args, **kwargs):
        return self._search("name", *args, **kwargs)

    def search_by_author(self, *args, **kwargs):
        return self._search("user", *args, **kwargs)
