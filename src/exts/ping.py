import disnake
from disnake.ext import plugins as p

from src.bot import Bot

plugin = p.Plugin[Bot](slash_command_attrs={"default_member_permissions": disnake.Permissions(administrator=True)})



@plugin.slash_command()
async def ping(inter: disnake.CommandInteraction, member: disnake.Member):
    """Ping a user"""
    try:
        await member.send(f"```**Your attention is needed in your ticket!** Please visit your ticket by clicking the link below:```\n\n{inter.channel.jump_url}")
        await inter.send(f"Pong! {member.mention}", ephemeral=True)

    except Exception as e:
        await inter.send(f"Unable to ping {member.mention}", ephemeral=True)


setup, teardown = plugin.create_extension_handlers()

