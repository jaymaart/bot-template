import disnake
from src.db.models import Queue, QueueConfig
import datetime as dt

class QueueManager:
    def __init__(self, bot): 
        self.bot = bot

    async def add_user(self, name: str, user_id: int, product: str, position: int):
        await Queue.create(user_id=user_id, name=name, product=product, position=position)
        await self.update_embed()

    async def remove_user(self, user_id: int):
        await Queue.filter(user_id=user_id).delete()
        await self.update_embed()

    async def update_embed(self):
        current_queue = await Queue.all()
        user_list = "\n".join([f"{i + 1}. {'<a:Green:1286111140794859603>' if i == 0 else '<a:Yellow:1286111791851634799>'} <@{user.user_id}> - {user.product}" for i, user in enumerate(current_queue)])
        queue_config = await QueueConfig.first()
        if not queue_config:
            embed = await self.create_embed()
            msg = await self.bot.get_channel(1276323493738319983).send(embed=embed)
            return await QueueConfig.create(channel_id=1276323493738319983, message_id=msg.id)
        
        msg = await self.bot.get_channel(queue_config.channel_id).fetch_message(queue_config.message_id)
        embed = msg.embeds[0]
        embed.description = f"{user_list}\n\nLast updated: <t:{int(dt.datetime.now().timestamp())}:R>"
        await self.send_embed(embed, msg)

    async def create_embed(self):
        embed = disnake.Embed(title="Void Studios Queue", description=f"Last updated: <t:{int(dt.datetime.now().timestamp())}:R>", color=disnake.Color.blurple())
        return embed

    async def send_embed(self, embed: disnake.Embed, msg: disnake.Message):
        await msg.edit(embed=embed)

    async def get_new_position(self):
        current_queue = await Queue.all()
        if len(current_queue) < 1:
            return 1
        else:
            return len(current_queue) + 1
        
    async def clear_queue(self):
        await Queue.all().delete()
        await self.update_embed()
