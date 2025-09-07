1. Installing the dependencies:
```bash
python3 -m pip install poetry
poetry install
```
2. Create a `.env` file in the root directory and add the following:
```env
TOKEN=YOUR_BOT_TOKEN
```
3. Configure the review system by editing `src/constants.py` and adding your ticket category IDs to the `Reviews.ticket_categories` tuple:
```python
class Reviews:
    """Review system configuration."""

    # Category IDs where tickets are created (add your ticket category IDs here)
    ticket_categories: tuple[int, ...] = (
        123456789012345678,  # Replace with your ticket category ID
        987654321098765432,  # Add more category IDs as needed
    )

    # Channel ID where public reviews will be posted
    public_review_channel_id: int | None = 123456789012345678  # Replace with your review channel ID
```
4. Run the bot: (Run `exit` to exit the shell.)
```bash
poetry shell
python main.py
```

## Review System Features

The bot now includes an automatic review system that:

- **Tracks ticket creation** by parsing the first message in ticket channels (extracts user from first mention)
- **Detects ticket closure** when channels are deleted
- **Sends review requests** via DM to the identified ticket creator
- **Collects ratings and comments** through interactive buttons and modals
- **Posts beautiful review cards** to a public review channel
- **Provides admin commands** to view statistics and manage reviews

### Admin Commands

- `/reviews stats` - View review statistics and ratings
- `/reviews list [limit]` - List recent reviews
- `/reviews associate [channel] [user]` - Manually associate a user with a ticket (fallback)
- `/reviews setchannel [channel]` - Set the public review channel

### Permissions Required

Make sure your bot has the following permissions:
- Send Messages
- Use Slash Commands
- Read Message History
- Read Messages/View Channels