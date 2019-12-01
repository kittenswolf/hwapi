# -*- coding: utf-8 -*-

from . import utils


def clean_string(s):
    return s.replace("\\", "")


class Character:

    def __init__(self, *, character_id):
        self.id = character_id

    def __str__(self):
        return {
            0: "Any",
            1: "Wheelchair Guy",
            2: "Segway Guy",
            3: "Irresponsible Dad",
            4: "Effective Shopper",
            5: "Moped Couple",
            6: "Lawnmower Man",
            7: "Explorer Guy",
            8: "Santa Claus",
            9: "Pogostick Man",
            10: "Irresponsible Mom",
            11: "Helicopter Man"
        }[self.id]


class User:

    def __init__(self, *, state, data):
        self._complete = False
        self._data = None

        self._state = state
        self._from_data(data)

    def _from_data(self, data):
        if not "active" in data:
            data["active"] = True

        if data["active"]:
            self.active = True

            self.name = data["name"]
            self.id = data["id"]

            self._date_joined = None
            self._email = None
            self._website = None
            self._location = None
            self._gender = None

            if "profile_table" in data:
                self._date_joined = data["profile_table"]["date joined"]

                if "email" in data["profile_table"]:
                    self._email = data["profile_table"]["email"]

                if "website" in data["profile_table"]:
                    self._website = data["profile_table"]["website"]

                if "location" in data["profile_table"]:
                    self._location = data["profile_table"]["location"]

                if "gender" in data["profile_table"]:
                    self._gender = data["profile_table"]["gender"]

                self._complete = True

            if self._complete:
                self._data = data
        else:
            self.active = False
            self._data = data

            self.name = None
            self.id = 0

            self._date_joined = None
            self._email = None
            self._website = None
            self._location = None
            self._gender = "unknown"

    async def _complete_data(self):
        user = await self._state.user(self.id)
        self._from_data(user._data)
        self._complete = True

    async def date_joined(self):
        if (self._date_joined != None or self._complete):
            return self._date_joined
        else:
            await self._complete_data()
            return self._date_joined

    async def email(self):
        if (self._email != None or self._complete):
            return self._email
        else:
            await self._complete_data()
            return self._email

    async def website(self):
        if (self._website != None or self._complete):
            return self._website
        else:
            await self._complete_data()
            return self._website

    async def location(self):
        if (self._location != None or self._complete):
            return self._location
        else:
            await self._complete_data()
            return self._location

    async def gender(self):
        if (self._gender != None or self._gender):
            return self._gender
        else:
            await self._complete_data()
            return self._gender

    def __eq__(self, other):
        if type(other) != type(self):
            return False
        else:
            return self.id == other.id

    def __ne__(self, other):
        return not self.__eq__(other)

    def levels(self, *args, **kwargs):
        return self._state.user_levels(self.id, *args, **kwargs)


class Level:

    def __init__(self, *, state, data):
        self._state = state
        self._from_data(data)

    def _from_data(self, data):
        self.date_published = data["@dp"]
        self.id = int(data["@id"])
        self.name = clean_string(data["@ln"])

        character = int(data["@pc"])
        self.character = Character(character_id=character)

        self.plays = int(data["@ps"])
        self.votes = int(data["@vs"])
        self.weighted_rating = float(data["@rg"])

        self.description = clean_string(data["uc"]) if data["uc"] else None

        user_id = int(data["@ui"])
        user_name = clean_string(data["@un"])
        author = {"name": user_name, "id": user_id}
        self.author = User(state=self._state, data=author)

        if "featured" in data:
            self.featured = True
        else:
            self.featured = self in self._state._featured_cache

        self._average_rating = None

    def __eq__(self, other):
        if type(other) != type(self):
            return False
        else:
            return self.id == other.id

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.id)

    @property
    def average_rating(self):
        if self._average_rating:
            return self._average_rating
        else:
            self._average_rating = utils.average_rating(self.weighted_rating, self.votes)
            return self._average_rating

    def replays(self, *args, **kwargs):
        return self._state.level_replays(self.id, *args, **kwargs)


class Replay:

    def __init__(self, *, state, data):
        self._complete = False
        self._data = None

        self._state = state
        self._from_data(data)

    def _from_data(self, data):
        patched_data = {}
        if not "rp" in data:
            patched_data = {}
            patched_data["rp"] = data
            data = patched_data

        if "lv" in data:
            self._level = Level(
                state=self._state,
                data=data["lv"]
            )
            self._complete = True
            self._data = data
        else:
            self._level = None
            self._complete = False

        self.date_created = data["rp"]["@dc"]
        self.id = int(data["rp"]["@id"])
        self.votes = int(data["rp"]["@vs"])
        self.weighted_rating = float(data["rp"]["@rg"])
        self.views = int(data["rp"]["@vw"])

        if int(data["rp"]["@ct"]) < 6000:
            self.completion_time = round(int(data["rp"]["@ct"]) / 30, 2)
        else:
            self.completion_time = None

        self.comment = clean_string(data["rp"]["uc"]) if data["rp"]["uc"] else None

        character = int(data["rp"]["@pc"])
        self.character = Character(character_id=character)

        user_id = int(data["rp"]["@ui"])
        user_name = clean_string(data["rp"]["@un"])
        author = {"name": user_name, "id": user_id}
        self.author = User(state=self._state, data=author)

        self._average_rating = None

    async def _complete_data(self):
        replay = await self._state.replay(self.id)
        self._from_data(user._data)
        self._complete = True

    @property
    def average_rating(self):
        if self._average_rating:
            return self._average_rating
        else:
            self._average_rating = utils.average_rating(self.weighted_rating, self.votes)
            return self._average_rating

    async def level(self):
        if (self._level != None or self._complete):
            return self._level
        else:
            await self._complete_data()
            return self._level
