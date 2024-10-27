import disnake
from disnake.ext import plugins as p
from src.bot import Bot

plugin = p.Plugin[Bot](slash_command_attrs={"default_member_permissions": disnake.Permissions(administrator=True)})


@plugin.slash_command()
async def queue(inter: disnake.CommandInteraction):
    pass

@queue.sub_command()
async def add(inter: disnake.CommandInteraction, member: disnake.Member, product: str, position: int = None):
    """Add a member to the queue"""
    position = position or await plugin.bot.queue_manager.get_new_position()
    await plugin.bot.queue_manager.add_user(member.name, member.id, product, position)
    await inter.send(f"Added {member.mention} to the queue for {product}", ephemeral=True)

@queue.sub_command()
async def remove(inter: disnake.CommandInteraction, member: disnake.Member, product: str, file: disnake.Attachment = None, url: str = None, dm: bool = False):
    """Remove a member from the queue"""
    try:
        action = file is not None and "file" or url is not None and "url" or "none"
        
        match action:
            case "file":
                if dm:
                    await member.send("```**You've been successfully removed from the Void Studios queue. Thank you for your support!**\nWe'd love to hear about your experience. If you have a moment, please consider leaving a vouch.\nYour feedback helps us improve and continue delivering top-notch service.\nLeave your vouch here: https://discord.com/channels/1175853430024192041/1286361860584636550```", file=file)
                    await inter.send(f"Removed {member.mention} from the queue for {product} and successfully DMed.", ephemeral=True)
                await plugin.bot.queue_manager.remove_user(member.id)
                await inter.send(f"Removed {member.mention} from the queue for {product}.", ephemeral=True)
                
            case "url":
                if dm:
                    await member.send(f"**You've been successfully removed from the Void Studios queue. Thank you for your support!**\nWe'd love to hear about your experience. If you have a moment, please consider leaving a vouch.\nYour feedback helps us improve and continue delivering top-notch service.\nLeave your vouch here: https://discord.com/channels/1175853430024192041/1286361860584636550\n\n Product: {url}")
                await plugin.bot.queue_manager.remove_user(member.id)
                await inter.send(f"Removed {member.mention} from the queue for {product} and successfully DMed.", ephemeral=True)
            case "none":
                if dm:
                    await member.send(f"**You've been successfully removed from the Void Studios queue. Thank you for your support!**\nWe'd love to hear about your experience. If you have a moment, please consider leaving a vouch.\nYour feedback helps us improve and continue delivering top-notch service.\nLeave your vouch here: https://discord.com/channels/1175853430024192041/1286361860584636550\n\n")
                await plugin.bot.queue_manager.remove_user(member.id)
                await inter.send(f"Removed {member.mention} from the queue for {product} and successfully DMed.", ephemeral=True)
       
    except Exception as e:
        await inter.send(f"Unable to remove {member.mention} from the queue for {product} possibly because their DMs are off.", ephemeral=True)

@queue.sub_command()
async def send_embed(inter: disnake.CommandInteraction):
    """Send the queue embed to the channel"""
    await plugin.bot.queue_manager.update_embed()
    await inter.send("Sent the queue embed to the channel", ephemeral=True)

@queue.sub_command()
async def update_embed(inter: disnake.CommandInteraction):
    """Update the queue embed"""
    await plugin.bot.queue_manager.update_embed()
    await inter.send("Updated the queue embed", ephemeral=True)

@queue.sub_command()
async def clear(inter: disnake.CommandInteraction):
    """Clear the queue"""
    await plugin.bot.queue_manager.clear_queue()
    await inter.send("Cleared the queue", ephemeral=True)

setup, teardown = plugin.create_extension_handlers()