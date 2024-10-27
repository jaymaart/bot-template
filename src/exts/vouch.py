import typing
import datetime as dt
import disnake
from disnake.ext import plugins as p
from src.bot import Bot
from src.db.models import Vouch

plugin = p.Plugin[Bot]()

@plugin.slash_command()
async def vouch(inter: disnake.CommandInteraction, vouch: str, rating: typing.Literal["1", "2", "3", "4", "5"]):
    """Leave a vouch"""
    star = "⭐"
    vouch_count = await Vouch.filter(user_id=inter.author.id).count()
    if vouch_count == 0:
        vouch_count = 1
    stars = star * int(rating)
    embed = disnake.Embed(title=f"Vouch #{vouch_count}", description=f"{stars}", color=disnake.Color.blurple())
    embed.add_field(name="Vouch", value=vouch)
    embed.set_thumbnail(url=inter.author.avatar.url)
    embed.set_footer(text=f"discord.gg/voidstudios", icon_url=inter.guild.me.avatar.url)
    embed.timestamp = dt.datetime.now()
    vouch = await Vouch.create(user_id=inter.author.id, vouch=vouch, rating=rating)
    await inter.send(embed=embed)

setup, teardown = plugin.create_extension_handlers()