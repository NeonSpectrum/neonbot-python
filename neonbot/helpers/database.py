from addict import Dict
from pymongo import MongoClient

from bot import env
from helpers import log

db = None


def load_database():
  global db

  username = env("DB_USER")
  password = env("DB_PASS")
  url = env("DB_HOST").split(":")
  name = env("DB_NAME")

  client = MongoClient(host=url[0],
                       port=int(url[1]),
                       username=username,
                       password=password,
                       authSource=name,
                       retryWrites=False)
  log.info(f"MongoDB connection established on {':'.join(url)}")

  db = client[name]


def process_database(guilds):
  for guild in guilds:
    count = db.servers.find({"server_id": str(guild.id)}).count

    if (count == 0):
      create_collection(guild.id)


def create_collection(guild_id):
  db.servers.insert_one({
    "server_id": str(guild_id),
    "prefix": env("PREFIX"),
    "deleteoncmd": False,
    "strictmode": False,
    "aliases": [],
    "channel": {},
    "music": {
      "volume": 100,
      "autoplay": False,
      "repeat": 'off',
      "autoresume": False,
      "roles": {}
    }
  })
  db.servers.insert_one({"status": "online", "game": {"type": "WATCHING", "name": "NANI?!"}})


class Database:
  def __init__(self, guild_id=None):
    if guild_id:
      self.guild_id = str(guild_id)
      self.refresh_config()
    self.refresh_settings()

  def refresh_config(self):
    self.config = Dict(db.servers.find_one({"server_id": self.guild_id}))
    return self

  def update_config(self):
    if isinstance(self.config, Dict):
      self.config = self.config.to_dict()
    db.servers.update_one({"server_id": self.guild_id}, {"$set": self.config})
    return self.refresh_config()

  def refresh_settings(self):
    self.settings = Dict(db.settings.find_one())
    return self

  def update_settings(self):
    if isinstance(self.settings, Dict):
      self.settings = self.settings.to_dict()
    db.settings.update_one({}, {"$set": self.settings})
    return self.refresh_settings()
