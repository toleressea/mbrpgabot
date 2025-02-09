# Bible Reading Plan Bot

A Discord bot that helps manage Bible reading plans in your server. The bot can manage multiple reading plans per channel, with support for pausing, resuming, and tracking progress.

## Features

- Start multiple reading plans in any channel
- Daily reading notifications with pause/resume support
- Automatic plan cycling (restarts from day 1 after completion)
- View current readings and plan progress
- Links to source materials

## Installation

1. Clone the repository:
```bash
git clone https://github.com/toleressea/mbrpgabot.git
cd mbrpgabot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file from the sample:
```bash
cp .env.sample .env
```

4. Edit `.env` and add your Discord bot token:
```
TOKEN=your_discord_bot_token_here
```

## Usage

Start the bot:
```bash
# Regular mode - responds to commands
python bot.py

# Publish mode - sends daily readings and increments days
python bot.py --publish
```

### Commands

- `!plans` - List all active reading plans in the channel
- `!start <type>` - Start a new reading plan in the current channel (shows first reading immediately)
- `!stop <type>` - Stop and remove a reading plan
- `!readings <type>` - Get the current reading for the plan
- `!set <type> <day>` - Set the current day for a reading plan
- `!pause <type>` - Pause the specified reading plan
- `!resume <type>` - Resume a paused reading plan

### Publish Mode Behavior

When running in publish mode (`--publish`), the bot will:
1. Send the current day's reading for all registered plans
2. Increment the day counter for non-paused plans
3. Automatically wrap to day 1 when a plan completes
4. Exit after publishing all readings

Paused plans will:
- Be marked with "(Paused)" in the daily reading message
- Not have their day counter incremented
- Continue from their last position when resumed

To automatically publish readings every day, you can use cron. For example, to publish at 6:00 AM server time every day:

1. Open your crontab:
```bash
crontab -e
```

2. Add this line (adjust the paths to match your setup):
```bash
0 6 * * * cd /path/to/mbrpgabot && /usr/bin/python3 bot.py --publish
```

Make sure:
- The paths to both the bot directory and python are absolute
- The `.env` file is in the bot directory
- The user running cron has permission to access all required files

### Reading Plans

Reading plans are defined in JSON files in the `plans/` directory. Each plan should have:
- A unique identifier (the filename without .json)
- Name
- Source link (optional)
- List of daily readings

Example plan format:
```json
{
    "name": "M'Cheyne Bible Reading Plan",
    "source_link": "https://www.mcheyne.info/calendar.pdf",
    "readings": [
        ["Genesis 1", "Matthew 1", "Ezra 1", "Acts 1"],
        ["Genesis 2", "Matthew 2", "Ezra 2", "Acts 2"]
    ]
}
```

The number of entries in the `readings` array determines the length of the plan. When a plan reaches its final day, it will automatically restart from day 1 on the next increment.

## Database

The bot uses SQLite to store:
- Active reading plans
- Current day for each plan (0-based internally, 1-based in commands)
- Pause status
- Channel associations

The database is automatically created on first run.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
