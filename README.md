# Bible Reading Plan Bot

A Discord bot that helps manage Bible reading plans in your server. The bot can manage multiple reading plans per channel, with support for pausing, resuming, and tracking progress.

## Features

- Start multiple reading plans in any channel
- Daily reading notifications
- Pause and resume reading plans
- Set current day for each plan
- View current readings
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
# Regular mode
python bot.py

# Publish mode (sends daily readings and exits)
python bot.py --publish
```

### Commands

- `!plans` - List all active reading plans in the channel
- `!start <type>` - Start a new reading plan in the current channel
- `!stop <type>` - Stop and remove a reading plan
- `!readings <type>` - Get the current reading plan for the channel
- `!set <type> <day>` - Set the current day for a reading plan
- `!pause <type>` - Pause the specified reading plan
- `!resume <type>` - Resume a paused reading plan

## Reading Plans

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

## Database

The bot uses SQLite to store:
- Active reading plans
- Current day for each plan
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
