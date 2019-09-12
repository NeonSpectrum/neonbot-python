import logging
from os import listdir
from os.path import isfile, join

import discord
from aiohttp import ClientSession, ClientTimeout
from discord.ext import commands

from . import Database, __title__, __version__, env
from .helpers.constants import LOGO
from .helpers.log import cprint

log = logging.getLogger(__name__)


class Bot(commands.Bot):
    def __init__(self):
        self.start_message()

        self.default_prefix = env("DEFAULT_PREFIX", ".")
        self.db = Database()
        self.session = ClientSession(timeout=ClientTimeout(total=30))

        self.app_info = None
        self.commands_executed = 0

        super().__init__(
            command_prefix=self.get_command_prefix(),
            activity=self.get_activity(),
            owner_ids=set(env.list("OWNER_IDS", [], subcast=int)),
        )

    def start_message(self):
        cprint(LOGO, "blue")
        log.info(f"Starting {__title__} v{__version__}")

    def get_activity(self):
        settings = self.db.get_settings().settings
        activity_type = settings.game.type.lower()
        activity_name = settings.game.name
        status = settings.status

        return discord.Activity(
            name=activity_name,
            type=discord.ActivityType[activity_type],
            status=discord.Status[status],
        )

    async def get_app_info(self):
        bot.app_info = await bot.application_info()
        return bot.app_info

    def get_command_prefix(self):
        return (
            lambda _, message: self.db.get_guild(message.guild.id).config.prefix
            if message.guild
            else env("DEFAULT_PREFIX", ".")
        )

    def load_cogs(self):
        cogs_dir = "neonbot/cogs"
        for extension in [
            f.replace(".py", "")
            for f in listdir(cogs_dir)
            if f != "__init__.py" and isfile(join(cogs_dir, f))
        ]:
            self.load_extension("neonbot.cogs." + extension)

    async def logout(self):
        await self.session.close()
        return super().logout()

    def run(self):
        self.load_cogs()
        super().run(env("TOKEN"))


bot = Bot()
