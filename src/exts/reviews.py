import datetime as dt
from typing import Optional

import disnake
from disnake import ui
from disnake.ext import commands

from src import constants, log
from src.db.models import Review, Ticket

logger = log.get_logger(__name__)


class ReviewView(ui.View):
    """Interactive view for collecting user reviews."""

    def __init__(self, ticket: Ticket, timeout: float = 300.0):
        super().__init__(timeout=timeout)
        self.ticket = ticket
        self.rating = None
        self.comment = None

    @ui.button(label="⭐", style=disnake.ButtonStyle.primary, custom_id="rating_1")
    async def rate_1_star(self, button: ui.Button, interaction: disnake.MessageInteraction):
        await self.handle_rating(interaction, 1)

    @ui.button(label="⭐⭐", style=disnake.ButtonStyle.primary, custom_id="rating_2")
    async def rate_2_stars(self, button: ui.Button, interaction: disnake.MessageInteraction):
        await self.handle_rating(interaction, 2)

    @ui.button(label="⭐⭐⭐", style=disnake.ButtonStyle.primary, custom_id="rating_3")
    async def rate_3_stars(self, button: ui.Button, interaction: disnake.MessageInteraction):
        await self.handle_rating(interaction, 3)

    @ui.button(label="⭐⭐⭐⭐", style=disnake.ButtonStyle.primary, custom_id="rating_4")
    async def rate_4_stars(self, button: ui.Button, interaction: disnake.MessageInteraction):
        await self.handle_rating(interaction, 4)

    @ui.button(label="⭐⭐⭐⭐⭐", style=disnake.ButtonStyle.primary, custom_id="rating_5")
    async def rate_5_stars(self, button: ui.Button, interaction: disnake.MessageInteraction):
        await self.handle_rating(interaction, 5)

    async def handle_rating(self, interaction: disnake.MessageInteraction, rating: int):
        """Handle rating selection and prompt for comment."""
        self.rating = rating

        embed = disnake.Embed(
            title="📝 Add a Comment (Optional)",
            description="Would you like to leave a comment with your review?",
            color=constants.Color.BLUE,
        )

        view = CommentView(self.ticket, rating)
        await interaction.response.edit_message(embed=embed, view=view)

    @ui.button(label="Skip Review", style=disnake.ButtonStyle.secondary, custom_id="skip")
    async def skip_review(self, button: ui.Button, interaction: disnake.MessageInteraction):
        """Allow user to skip the review."""
        embed = disnake.Embed(
            title="Review Skipped",
            description="Thank you for your feedback! Your review request has been dismissed.",
            color=constants.Color.GREY,
        )

        # Mark review as sent to prevent future requests
        self.ticket.review_sent = True
        await self.ticket.save()

        await interaction.response.edit_message(embed=embed, view=None, delete_after=10)


class CommentView(ui.View):
    """View for collecting optional review comments."""

    def __init__(self, ticket: Ticket, rating: int, timeout: float = 300.0):
        super().__init__(timeout=timeout)
        self.ticket = ticket
        self.rating = rating

    @ui.button(label="Add Comment", style=disnake.ButtonStyle.primary, custom_id="add_comment")
    async def add_comment(self, button: ui.Button, interaction: disnake.MessageInteraction):
        """Prompt user to enter a comment via modal."""
        modal = ReviewCommentModal(self.ticket, self.rating)
        await interaction.response.send_modal(modal)

    @ui.button(label="No Comment", style=disnake.ButtonStyle.secondary, custom_id="no_comment")
    async def no_comment(self, button: ui.Button, interaction: disnake.MessageInteraction):
        """Submit review without comment."""
        await self.submit_review(interaction, comment=None)

    async def submit_review(self, interaction: disnake.MessageInteraction, comment: Optional[str]):
        """Submit the review to database."""
        # Create review in database
        review = await Review.create(
            ticket=self.ticket,
            user_id=self.ticket.user_id,
            rating=self.rating,
            comment=comment,
        )

        # Mark ticket as reviewed
        self.ticket.review_sent = True
        await self.ticket.save()

        # Send confirmation to user
        embed = disnake.Embed(
            title="✅ Review Submitted!",
            description=f"Thank you for your feedback!\n\n**Rating:** {review.get_star_rating()}",
            color=constants.Color.GREEN,
        )

        if comment:
            embed.add_field(name="Comment", value=comment, inline=False)

        await interaction.response.edit_message(embed=embed, view=None, delete_after=15)

        # Post to public review channel
        await self.post_public_review(review)


class ReviewCommentModal(ui.Modal):
    """Modal for collecting review comments."""

    def __init__(self, ticket: Ticket, rating: int):
        self.ticket = ticket
        self.rating = rating

        self.comment = ui.TextInput(
            label="Your Comment",
            placeholder="Tell us about your experience...",
            style=disnake.TextInputStyle.paragraph,
            max_length=1000,
            required=False,
            custom_id="review_comment_input",
        )

        super().__init__(
            title="Leave a Comment", 
            custom_id="review_comment_modal",
            components=[self.comment]
        )

    async def callback(self, interaction: disnake.ModalInteraction):
        """Handle modal submission."""
        comment = self.comment.value.strip() if self.comment.value else None

        # Create review in database
        review = await Review.create(
            ticket=self.ticket,
            user_id=self.ticket.user_id,
            rating=self.rating,
            comment=comment,
        )

        # Mark ticket as reviewed
        self.ticket.review_sent = True
        await self.ticket.save()

        embed = disnake.Embed(
            title="✅ Review Submitted!",
            description=f"Thank you for your feedback!\n\n**Rating:** {review.get_star_rating()}",
            color=constants.Color.GREEN,
        )

        if comment:
            embed.add_field(name="Comment", value=comment, inline=False)

        await interaction.response.edit_message(embed=embed, view=None)

        # Post to public review channel
        # We need to get the bot instance from the interaction
        cog = interaction.bot.get_cog("Reviews")
        if cog:
            await cog.post_public_review(review)


class Reviews(commands.Cog):
    """Cog for handling ticket review system."""

    def __init__(self, bot: commands.AutoShardedInteractionBot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        """Listen for the first message in ticket channels to identify ticket creators."""
        # Only process bot messages (ticket system messages)
        if not message.author.bot:
            return

        # Check if this is a ticket channel
        if not constants.Reviews.ticket_categories:
            return

        if not isinstance(message.channel, disnake.TextChannel):
            return

        if message.channel.category_id not in constants.Reviews.ticket_categories:
            return

        # Check if we already have a ticket record for this channel
        existing_ticket = await Ticket.get_or_none(channel_id=message.channel.id)
        if existing_ticket:
            return  # Ticket already tracked

        # Parse user mentions from the message content
        # Format: @Jaymart @Developer @Owner @Support
        # We want the first user mention (not role mentions)
        user_mentions = [user for user in message.mentions if not user.bot]
        
        if user_mentions:
            ticket_creator_id = user_mentions[0].id  # First user mention is the ticket creator

            # Create ticket record
            ticket = await Ticket.create(
                channel_id=message.channel.id,
                user_id=ticket_creator_id,
                category_id=message.channel.category_id,
            )

            logger.info(f"Created ticket record for user {ticket_creator_id} ({user_mentions[0].name}) in channel {message.channel.name}")
        else:
            # Fallback: parse raw content for user IDs if mentions aren't populated
            import re
            user_id_pattern = r'<@(\d+)>'
            user_ids = re.findall(user_id_pattern, message.content)
            
            if user_ids:
                # Get the first user ID and verify it's a real user (not a role)
                try:
                    first_user_id = int(user_ids[0])
                    user = await self.bot.get_or_fetch_user(first_user_id)
                    
                    if user and not user.bot:
                        # Create ticket record
                        ticket = await Ticket.create(
                            channel_id=message.channel.id,
                            user_id=first_user_id,
                            category_id=message.channel.category_id,
                        )

                        logger.info(f"Created ticket record for user {first_user_id} ({user.name}) in channel {message.channel.name}")
                    else:
                        logger.warning(f"First mention in ticket channel {message.channel.name} is not a valid user")
                except (ValueError, disnake.NotFound):
                    logger.warning(f"Could not resolve first user ID from ticket channel {message.channel.name}")
            else:
                logger.warning(f"No user mentions found in first message of ticket channel {message.channel.name}")

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: disnake.abc.GuildChannel):
        """Listen for channel deletions to detect ticket closures."""
        if not isinstance(channel, disnake.TextChannel):
            return

        # Check if this channel was in a ticket category
        if not constants.Reviews.ticket_categories:
            return

        if channel.category_id not in constants.Reviews.ticket_categories:
            return

        logger.info(f"Detected ticket channel deletion: {channel.name} (ID: {channel.id})")

        # Find the ticket in database
        ticket = await Ticket.get_or_none(channel_id=channel.id)
        if not ticket:
            logger.warning(f"No ticket found for deleted channel {channel.id}")
            return

        # Update ticket with closure time
        ticket.closed_at = dt.datetime.now(tz=dt.timezone.utc)
        await ticket.save()

        # Check if review already sent
        if ticket.review_sent:
            logger.info(f"Review already sent for ticket {ticket.id}")
            return

        # Send review request to user
        await self.send_review_request(ticket)

    async def post_public_review(self, review: Review):
        """Post a review to the public review channel."""
        if not constants.Reviews.public_review_channel_id:
            logger.warning("No public review channel configured")
            return

        try:
            channel = self.bot.get_channel(constants.Reviews.public_review_channel_id)
            if not channel:
                logger.warning(f"Could not find public review channel {constants.Reviews.public_review_channel_id}")
                return

            # Get user info
            user = await self.bot.get_or_fetch_user(review.user_id)
            username = user.name if user else "Anonymous User"

            # Create a beautiful embed for the public review
            embed = disnake.Embed(
                title="⭐ New Review Received!",
                description=f"A user has shared their feedback about our support.",
                color=self.get_rating_color(review.rating),
                timestamp=review.created_at
            )

            # Add user info
            embed.add_field(
                name="👤 Customer",
                value=username,
                inline=True
            )

            # Add rating with visual representation
            embed.add_field(
                name="⭐ Rating",
                value=f"**{review.rating}/5**\n{review.get_star_rating()}",
                inline=True
            )

            # Add category info if available
            if review.ticket.category_id:
                category_emoji = self.get_category_emoji(review.ticket.category_id)
                embed.add_field(
                    name="📂 Category",
                    value=category_emoji,
                    inline=True
                )

            # Add comment if provided
            if review.comment:
                # Truncate long comments for embed
                comment = review.comment[:1000] + "..." if len(review.comment) > 1000 else review.comment
                embed.add_field(
                    name="💬 Feedback",
                    value=comment,
                    inline=False
                )

            # Add footer with review ID and helpful text
            embed.set_footer(
                text=f"Review #{review.id} • Thank you for your feedback!",
                icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None
            )

            # Add some flair based on rating
            if review.rating >= 4:
                embed.set_thumbnail(url="https://i.imgur.com/4M7IWzq.png")  # Positive feedback icon
            elif review.rating == 3:
                embed.set_thumbnail(url="https://i.imgur.com/X8m6QzN.png")  # Neutral feedback icon
            else:
                embed.set_thumbnail(url="https://i.imgur.com/9X8qQcF.png")  # Needs improvement icon

            await channel.send(embed=embed)
            logger.info(f"Posted public review #{review.id} to channel {channel.name}")

        except Exception as e:
            logger.error(f"Error posting public review: {e}")

    def get_rating_color(self, rating: int) -> disnake.Color:
        """Get appropriate color based on rating."""
        if rating >= 4:
            return disnake.Color.green()
        elif rating == 3:
            return disnake.Color.blue()
        else:
            return disnake.Color.red()

    def get_category_emoji(self, category_id: int) -> str:
        """Get appropriate emoji for ticket category."""
        # You can customize these based on your specific categories
        category_emojis = {
            1413644462944686081: "🎫 General Support",
            1413644883641766040: "⚡ Technical Support",
            1413645847442489354: "💰 Billing Support",
        }
        return category_emojis.get(category_id, "🎫 Support")

    async def send_review_request(self, ticket: Ticket):
        """Send a review request to the ticket creator."""
        try:
            user = await self.bot.get_or_fetch_user(ticket.user_id)
            if not user:
                logger.warning(f"Could not find user {ticket.user_id} for review request")
                return

            embed = disnake.Embed(
                title="🎫 Ticket Closed - Leave a Review!",
                description=(
                    "Your ticket has been closed! We'd love to hear about your experience.\n\n"
                    "Please take a moment to rate your support experience:"
                ),
                color=constants.Color.BLUE,
            )

            embed.add_field(
                name="Rating Scale",
                value="⭐ = Poor\n⭐⭐ = Below Average\n⭐⭐⭐ = Average\n⭐⭐⭐⭐ = Good\n⭐⭐⭐⭐⭐ = Excellent",
                inline=False
            )

            embed.set_footer(text="This review request will expire in 5 minutes")

            view = ReviewView(ticket)

            await user.send(embed=embed, view=view)
            logger.info(f"Sent review request to user {user.id} for ticket {ticket.id}")

        except disnake.Forbidden:
            logger.warning(f"Could not send DM to user {ticket.user_id} - DMs disabled")
            # Mark as sent to prevent retry
            ticket.review_sent = True
            await ticket.save()
        except Exception as e:
            logger.error(f"Error sending review request: {e}")

    @commands.slash_command(name="reviews", description="View review statistics and management")
    @commands.has_permissions(administrator=True)
    async def reviews_command(self, inter: disnake.ApplicationCommandInteraction):
        """Main command for viewing review statistics."""
        pass

    @reviews_command.sub_command(name="stats", description="View review statistics")
    async def reviews_stats(self, inter: disnake.ApplicationCommandInteraction):
        """Show review statistics."""
        # Get review statistics
        total_reviews = await Review.all().count()
        avg_rating = await Review.all().only("rating")

        if total_reviews == 0:
            embed = disnake.Embed(
                title="📊 Review Statistics",
                description="No reviews have been collected yet.",
                color=constants.Color.GREY,
            )
        else:
            # Calculate average rating
            ratings = [review.rating for review in avg_rating]
            average = sum(ratings) / len(ratings)

            # Get rating distribution
            distribution = {}
            for i in range(1, 6):
                distribution[i] = ratings.count(i)

            embed = disnake.Embed(
                title="📊 Review Statistics",
                color=constants.Color.BLUE,
            )

            embed.add_field(name="Total Reviews", value=str(total_reviews), inline=True)
            embed.add_field(name="Average Rating", value=f"{average:.1f} ⭐", inline=True)
            embed.add_field(name="Rating Distribution", value="\n".join([
                f"{'⭐' * i}: {count}" for i, count in distribution.items() if count > 0
            ]), inline=False)

        await inter.response.send_message(embed=embed, ephemeral=True)

    @reviews_command.sub_command(name="list", description="List recent reviews")
    async def reviews_list(
        self,
        inter: disnake.ApplicationCommandInteraction,
        limit: int = 10
    ):
        """List recent reviews."""
        if limit > 50:
            limit = 50

        reviews = await Review.all().prefetch_related("ticket").order_by("-created_at").limit(limit)

        if not reviews:
            embed = disnake.Embed(
                title="📝 Recent Reviews",
                description="No reviews found.",
                color=constants.Color.GREY,
            )
        else:
            embed = disnake.Embed(
                title="📝 Recent Reviews",
                color=constants.Color.BLUE,
            )

            for review in reviews:
                user = await self.bot.get_or_fetch_user(review.user_id)
                username = user.name if user else "Unknown User"

                review_text = f"**{username}**: {review.get_star_rating()}"
                if review.comment:
                    review_text += f"\n{review.comment[:100]}{'...' if len(review.comment) > 100 else ''}"

                embed.add_field(
                    name=f"Review #{review.id}",
                    value=review_text,
                    inline=False
                )

        await inter.response.send_message(embed=embed, ephemeral=True)

    @reviews_command.sub_command(
        name="associate",
        description="Manually associate a user with a ticket channel"
    )
    @commands.has_permissions(administrator=True)
    async def reviews_associate(
        self,
        inter: disnake.ApplicationCommandInteraction,
        channel: disnake.TextChannel,
        user: disnake.User
    ):
        """Manually associate a user with a ticket channel."""
        # Check if channel is in ticket category
        if channel.category_id not in constants.Reviews.ticket_categories:
            await inter.response.send_message(
                "❌ This channel is not in a configured ticket category.",
                ephemeral=True
            )
            return

        # Create or update ticket record
        ticket, created = await Ticket.get_or_create(
            channel_id=channel.id,
            defaults={
                "user_id": user.id,
                "category_id": channel.category_id,
            }
        )

        if not created:
            ticket.user_id = user.id
            await ticket.save()

        embed = disnake.Embed(
            title="✅ Ticket Associated",
            description=f"Successfully associated {user.mention} with ticket channel {channel.mention}",
            color=constants.Color.GREEN,
        )

        await inter.response.send_message(embed=embed, ephemeral=True)

    @reviews_command.sub_command(
        name="setchannel",
        description="Set the channel where public reviews will be posted"
    )
    @commands.has_permissions(administrator=True)
    async def reviews_setchannel(
        self,
        inter: disnake.ApplicationCommandInteraction,
        channel: disnake.TextChannel
    ):
        """Set the public review channel."""
        # Update the constant (this will persist until restart)
        constants.Reviews.public_review_channel_id = channel.id

        embed = disnake.Embed(
            title="✅ Review Channel Set",
            description=f"Public reviews will now be posted in {channel.mention}",
            color=constants.Color.GREEN,
        )

        embed.add_field(
            name="Channel ID",
            value=str(channel.id),
            inline=True
        )

        embed.add_field(
            name="Note",
            value="This setting will reset when the bot restarts. Update `constants.py` for permanent configuration.",
            inline=False
        )

        await inter.response.send_message(embed=embed, ephemeral=True)


def setup(bot: commands.AutoShardedInteractionBot) -> None:
    """Load the reviews cog."""
    bot.add_cog(Reviews(bot))
