import json
import logging
import os
import random
from time import time
from typing import cast

import aiohttp
import discord
import emoji
import psutil
import youtube_dl
from addict import Dict
from discord.ext import commands

from .. import __author__, __title__, __version__, bot, env
from ..classes import Embed
from ..helpers.date import date_format, format_seconds
from ..helpers.log import Log

log = cast(Log, logging.getLogger(__name__))


async def chatbot(message: discord.Message, dm: bool = False) -> None:
    if message.author.id not in bot.owner_ids:
        return

    with message.channel.typing():
        msg = message.content if dm else " ".join(message.content.split(" ")[1:])
        params = {
            "key": env.str('CLEVERBOT_API'),
            "input": emoji.demojize(msg)
        }

        if message.author.id in bot.chatbot and bot.chatbot[message.author.id]['time'] + 60 > time():
            params['cs'] = bot.chatbot[message.author.id]['cs']

        res = await bot.session.get(
            "https://www.cleverbot.com/getreply", params=params
        )
        response = Dict(await res.json())

        bot.chatbot[message.author.id] = {
            "cs": response.cs,
            "time": time()
        }
        await message.channel.send(
            embed=Embed(
                f"{'' if dm else message.author.mention} {response.output}"
            )
        )


class Utility(commands.Cog):
    @commands.command()
    async def chatbot(self, ctx: commands.Context) -> None:
        """Chat with a bot using program-o."""

        await chatbot(ctx.message)

    @commands.command()
    async def random(self, ctx: commands.Context, *args: str) -> None:
        """Picks a text in the given list."""

        await ctx.send(embed=Embed(random.choice(args)))

    @commands.command()
    async def say(self, ctx: commands.Context, *, text: str) -> None:
        """Says the text given."""

        await ctx.send(embed=Embed(text))

    @commands.command()
    async def speak(self, ctx: commands.Context, *, text: str) -> None:
        """Says the text given with TTS."""

        await ctx.send(text, tts=True, delete_after=0)

    @commands.command(aliases=["stats"])
    async def status(self, ctx: commands.Context) -> None:
        """Shows the information of the bot."""

        process = psutil.Process(os.getpid())

        embed = Embed()
        embed.set_author(f"{__title__} v{__version__}", icon_url=bot.user.avatar_url)
        embed.add_field("Username", bot.user.name)
        embed.add_field("Created On", f"{bot.user.created_at:%Y-%m-%d %I:%M:%S %p}")
        embed.add_field("Created By", __author__)
        embed.add_field("Guilds", len(bot.guilds))
        embed.add_field("Channels", sum(1 for _ in bot.get_all_channels()))
        embed.add_field("Users", len(bot.users))
        embed.add_field("Commands Executed", len(bot.commands_executed))
        embed.add_field(
            "Ram Usage",
            f"Approximately {(process.memory_info().rss / 1024000):.2f} MB",
            inline=True,
        )
        embed.add_field(
            "Uptime", format_seconds(time() - process.create_time()).split(".")[0]
        )
        embed.add_field(
            "Packages",
            f"""
            discord.py `{discord.__version__}`
            youtube-dl `{youtube_dl.version.__version__}`
            """
        )

        await ctx.send(embed=embed)

    @commands.command()
    @commands.is_owner()
    async def sms(self, ctx: commands.Context, number: str, *, message: str) -> None:
        print(number, message)
        def generate_embed():
            embed = Embed()
            embed.set_author(name="✉ SMS")
            embed.set_footer(
                text="Powered by Twilio",
                icon_url="https://assets.twilio.com/public_assets/console-js/2.9.0/images/favicons/Twilio_72.png"
            )
            embed.add_field("To:", number, inline=True)
            embed.add_field("Body:", message, inline=True)

            return embed

        msg = await ctx.send(embed=generate_embed().add_field("Status:", "Sending...", inline=False))

        account_sid = env.str("TWILIO_ACCOUNT_SID")
        auth_token = env.str("TWILIO_AUTH_TOKEN")

        body = f"{message}\n\nSent by {ctx.author} using {__title__}"

        response = await bot.session.post(
            f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json",
            auth=aiohttp.BasicAuth(login=account_sid, password=auth_token),
            data={"From": env.str("TWILIO_NUMBER"), "To": number, "Body": body}
        )

        response = Dict(await response.json())

        if response.status >= 400:
            await msg.edit(
                embed=generate_embed().add_field("Status:", "Sending failed.", inline=False)
                                      .add_field("Reason:", response.message, inline=False)
                                      .add_field("Date sent:", date_format(), inline=False)
            )
        else:
            await msg.edit(
                embed=generate_embed().add_field("Status:", "Sent", inline=False)
                                      .add_field("Date sent:", date_format(), inline=False)
            )


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Utility())
