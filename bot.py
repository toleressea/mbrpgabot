import discord
import json
import os
import db
from discord.ext import commands
import argparse

# Set up the CLI
parser = argparse.ArgumentParser()
parser.add_argument('-p', '--publish', action='store_true', help='Publish reading plans to registered channels')
args = parser.parse_args()

# Parse the .env for env vars
with open('.env', 'r') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#'):
            key, value = line.split('=', 1)
            os.environ[key.strip()] = value.strip()

# Load the plans
PLANS = {os.path.splitext(p)[0]: json.load(open(f"plans/{p}", 'r')) for p in os.listdir('plans') if p.endswith('.json')}

# Prepare the bot
intents = discord.Intents.default()
intents.typing = False
intents.presences = False
intents.message_content = True
bot = commands.Bot(intents=intents, command_prefix='!')

# Optionally publish reading plans to registered channels
@bot.event
async def on_ready():
    if args.publish and bot.is_ready():
        registered_plans = db.get_all_plans()
        for plan in registered_plans:
            ctx = bot.get_channel(plan["channel_id"])

            # Increment the day if the plan is not paused
            if not plan["paused"]:
                plan['current_day'] += 1
                # Wrap to 0 if we've exceeded the plan length
                plan['current_day'] = normalize_day(plan['current_day'], plan['plan_type'])
                db.update_plan(plan["id"], current_day=plan["current_day"])

            await send_daily_reading(ctx, plan)
            
        await bot.close()

class BibleReadingBotHelp(commands.MinimalHelpCommand):
    async def send_bot_help(self, mapping):
        embed = discord.Embed(
            title="Bible Reading Plan Bot Commands",
            color=discord.Color.blurple()
        )
        
        commands_text = """
• `!plans` - List all active reading plans in this channel
• `!start <type>` - Start a new reading plan in the current channel
• `!stop <type>` - Stop and remove a reading plan
• `!readings <type>` - Get the current reading plan for the channel
• `!set <type> <day>` - Set the current day for a reading plan
• `!pause <type>` - Pause the specified reading plan
• `!resume <type>` - Resume a paused reading plan
"""
        embed.add_field(name="Available Commands", value=commands_text, inline=False)
        
        plans_text = ""
        for plan_type, plan_content in PLANS.items():
            source_link = f" ([source]({plan_content['source_link']}))" if 'source_link' in plan_content else ""
            plans_text += f"• `{plan_type}` - {plan_content['name']}{source_link}\n"
        
        embed.add_field(name="Available Reading Plans", value=plans_text, inline=False)
        
        channel = self.get_destination()
        await channel.send(embed=embed)

bot.help_command = BibleReadingBotHelp()

# Helper functions
def format_plan_name(plan_content: dict) -> str:
    """Format plan name with source link if available"""
    name = plan_content["name"]
    return f'[{name}]({plan_content["source_link"]})' if 'source_link' in plan_content else name

def get_plan_content(plan_type: str):
    """Get plan content and validate plan type exists"""
    plan_type = plan_type.lower()
    if plan_type not in PLANS:
        return None
    return PLANS[plan_type]

def get_plan_length(plan_type: str) -> int:
    """Get the number of days in a reading plan"""
    return len(PLANS[plan_type]["readings"])

def normalize_day(day: int, plan_type: str) -> int:
    """Normalize the day to be within the plan's length.
    Only wraps to 0 if the day exceeds the plan length."""
    plan_length = get_plan_length(plan_type)
    if day >= plan_length:
        return 0
    return day

async def send_daily_reading(ctx, plan: dict) -> str:
    """Get formatted daily reading message for a plan"""
    day = plan["current_day"]
    plan_content = PLANS[plan["plan_type"]]  # Now using plan_type from db
    paused_text = " (Paused)" if plan["paused"] else ""

    reading_header = f'{format_plan_name(plan_content)}, Daily Reading {day + 1}{paused_text} --'
    readings = plan_content["readings"][day]

    p_type = plan_content['type']
    if p_type == 'bible_calendar':
        await ctx.send(f'{reading_header} **{", ".join(readings)}**')
    elif p_type == 'book':
        await ctx.send(f'**{reading_header}**')
        for reading in readings:        
            # Split text into chunks of max 2000 chars (Discord limit)
            chunks = []
            current_chunk = []
            current_length = 0
            
            # Split by words to avoid breaking words
            words = reading.split()
            for word in words:
                # Add 1 for the space after the word
                word_length = len(word) + 1
                
                # If adding this word would exceed limit, start new chunk
                if current_length + word_length > 2000 and current_chunk:
                    chunks.append(' '.join(current_chunk))
                    current_chunk = []
                    current_length = 0
                
                current_chunk.append(word)
                current_length += word_length
            
            # Add remaining text as final chunk
            if current_chunk:
                chunks.append(' '.join(current_chunk))
            
            # Send header and chunks
            for chunk in chunks:
                await ctx.send(chunk)
    else:
        await ctx.send(f'Unsupported plan type: {p_type}')

async def validate_plan(ctx, plan_type: str, check_exists: bool = True) -> tuple:
    """Validate plan type and get plan data. Returns (plan_content, plan) tuple.
    
    If check_exists is True, verifies the plan exists in the channel.
    If check_exists is False, verifies the plan doesn't exist in the channel.
    """
    plan_content = get_plan_content(plan_type)
    if not plan_content:
        await ctx.send(f'`{plan_type}` is not a supported plan!')
        return None, None
        
    plan = db.get_plan_by_channel_and_type(ctx.message.channel.id, plan_type)
    
    if check_exists and not plan:
        await ctx.send(f'{format_plan_name(plan_content)} not running for this channel!')
        return None, None
    elif not check_exists and plan:
        await ctx.send(f'{format_plan_name(plan_content)} already running in this channel!')
        return None, None
        
    return plan_content, plan

# Define bot commands
@bot.command()
async def plans(ctx):
    """Lists all active reading plans in the current channel"""
    plans = db.get_plans_by_channel(ctx.message.channel.id)

    if plans:
        message = ''
        for p in plans:
            plan_content = PLANS[p["plan_type"]]  # Now using plan_type from db
            message += f'{format_plan_name(plan_content)} (`{p["plan_type"]}`): Current Day - {p["current_day"] + 1}, Paused - {"Yes" if p["paused"] else "No"}\n'
    else:
        message = 'No reading plans found. Try adding one with !start <type> from the following list:\n'
        for plan_type, plan_content in PLANS.items():
            message += f'- `{plan_type}` ({format_plan_name(plan_content)})\n'
            
    await ctx.send(message)

@bot.command()
async def start(ctx, plan_type: str):
    """Start a new reading plan in the current channel"""
    plan_content, _ = await validate_plan(ctx, plan_type, check_exists=False)
    if plan_content:
        plan_id = db.create_plan(ctx.message.channel.id, plan_type)
        await ctx.send(f'{format_plan_name(plan_content)} started!')

        # Also post the reading for the newly started plan
        plan = db.get_plan(plan_id)
        await send_daily_reading(ctx, plan)

@bot.command()
async def pause(ctx, plan_type: str):
    """Pause a reading plan to temporarily stop receiving daily readings"""
    plan_content, plan = await validate_plan(ctx, plan_type)
    if plan:
        if plan['paused']:
            await ctx.send(f'{format_plan_name(plan_content)} is already paused!')
            return

        db.update_plan(plan['id'], paused=True)
        await ctx.send(f'{format_plan_name(plan_content)} paused!')

@bot.command()
async def resume(ctx, plan_type: str):
    """Resume a previously paused reading plan"""
    plan_content, plan = await validate_plan(ctx, plan_type)
    if plan:
        if not plan['paused']:
            await ctx.send(f'{format_plan_name(plan_content)} is not paused!')
            return
        
        db.update_plan(plan['id'], paused=False)
        await ctx.send(f'{format_plan_name(plan_content)} resumed!')

@bot.command()
async def set(ctx, plan_type: str, day: int):
    """Set the current day for a reading plan"""
    plan_content, plan = await validate_plan(ctx, plan_type)
    if plan:
        # Convert to 0-based index and normalize
        zero_based_day = day - 1
        plan_length = get_plan_length(plan_type)
        
        if zero_based_day >= plan_length:
            normalized_day = 0
            await ctx.send(f'{format_plan_name(plan_content)} set to day 1 (wrapped around from {day}, plan length is {plan_length})')
        else:
            normalized_day = zero_based_day
            await ctx.send(f'{format_plan_name(plan_content)} set to day {day}!')
            
        db.update_plan(plan['id'], current_day=normalized_day)

@bot.command()
async def readings(ctx):
    """Get the current reading plan for the channel"""
    plans = db.get_plans_by_channel(ctx.message.channel.id)
    if not plans:
        await ctx.send('No reading plans found!')
        return

    for plan in plans:
        await send_daily_reading(ctx, plan)

@bot.command()
async def stop(ctx, plan_type: str):
    """Stop and remove a reading plan from the channel"""
    plan_content, plan = await validate_plan(ctx, plan_type)
    if plan:
        db.delete_plan(plan['id'])
        await ctx.send(f'{format_plan_name(plan_content)} stopped!')

bot.run(os.environ['TOKEN'])
