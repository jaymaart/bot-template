from tortoise import fields
from tortoise.models import Model


class Ticket(Model):
    """Model to track ticket information for review system."""

    id = fields.IntField(pk=True)
    channel_id = fields.BigIntField(unique=True, description="Discord channel ID")
    user_id = fields.BigIntField(description="User who created the ticket")
    category_id = fields.BigIntField(description="Category where ticket was created")
    created_at = fields.DatetimeField(auto_now_add=True)
    closed_at = fields.DatetimeField(null=True)
    review_sent = fields.BooleanField(default=False)

    class Meta:
        table = "tickets"


class Review(Model):
    """Model to store user reviews after ticket closure."""

    id = fields.IntField(pk=True)
    ticket = fields.OneToOneField("models.Ticket", related_name="review", on_delete=fields.CASCADE)
    user_id = fields.BigIntField(description="User who left the review")
    rating = fields.IntField(description="Rating from 1-5 stars")
    comment = fields.TextField(null=True, description="Optional review comment")
    created_at = fields.DatetimeField(auto_now_add=True)
    anonymous = fields.BooleanField(default=False)

    class Meta:
        table = "reviews"

    def get_star_rating(self) -> str:
        """Return star representation of rating."""
        stars = "⭐" * self.rating
        empty_stars = "☆" * (5 - self.rating)
        return f"{stars}{empty_stars}"
