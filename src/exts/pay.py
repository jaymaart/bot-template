import disnake
from disnake.ext import plugins as p
from src.db.models import Payment

from src.bot import Bot

plugin = p.Plugin[Bot](slash_command_attrs={"default_member_permissions": disnake.Permissions(administrator=True)})

@plugin.slash_command()
async def pay(inter: disnake.CommandInteraction):
    """Payment Options"""


@pay.sub_command()
async def add(inter: disnake.CommandInteraction, name: str, url: str, image_url: str = None):
    """Add a payment option
    
    Parameters
    ----------
    payment: str
        The name of the payment option
    url: str
        The URL of the payment option i.e https://paypal.me/username
    image_url: str
        The URL of the image of the payment option
    """
    if image_url:
        await Payment.create(name=name, url=url, image=image_url)
    else:
        await Payment.create(name=name, url=url)
    await inter.send(f"Added {name} to payment options", ephemeral=True)

@pay.sub_command()
async def remove(inter: disnake.CommandInteraction, name: str):
    """Remove a payment option
    
    Parameters
    ----------
    name: str
        The name of the payment option
    """
    await Payment.filter(name=name).delete()
    await inter.send(f"Removed {name} from payment options", ephemeral=True)

@pay.sub_command()
async def send(inter: disnake.CommandInteraction, name: str):
    """Send a payment option to a user
    
    Parameters
    ----------
    name: str
        The name of the payment option
    """
    payment = await Payment.filter(name=name).first()
    if not payment:
        await inter.send(f"Payment option {name} not found", ephemeral=True)
        return
    embed = disnake.Embed(title=payment.name, description=f"{payment.url}\n\n{payment.description if not "None" else ''}", color=disnake.Color.blurple())
    if payment.image:
        embed.set_image(url=payment.image)
    await inter.send(embed=embed, ephemeral=True)

@send.autocomplete("name")
@remove.autocomplete("name")
async def send_autocomplete(inter: disnake.CommandInteraction, name: str):
    payments = await Payment.all()
    return [payment.name for payment in payments]

setup, teardown = plugin.create_extension_handlers()