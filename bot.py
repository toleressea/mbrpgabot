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
            message_channel = bot.get_channel(plan["channel_id"])
            await message_channel.send(get_daily_reading(plan))
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
• `!reading <type>` - Get the current reading plan for the channel
• `!set <type> <day>` - Set the current day for a reading plan
• `!pause <type>` - Pause the specified reading plan
• `!resume <type>` - Resume a paused reading plan
"""
        embed.add_field(name="Available Commands", value=commands_text, inline=False)
        
        plans_text = ""
        for plan_type, plan_data in PLANS.items():
            source_link = f" ([source]({plan_data['source_link']}))" if 'source_link' in plan_data else ""
            plans_text += f"• `{plan_type}` - {plan_data['name']}{source_link}\n"
        
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

def get_daily_reading(plan: dict) -> str:
    """Get formatted daily reading message for a plan"""
    day = plan["current_day"]
    plan_content = PLANS[plan["plan_type"]]  # Now using plan_type from db
    return f'{format_plan_name(plan_content)}, Daily Reading {day + 1} -- **{", ".join(plan_content["readings"][day])}**'

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
        db.create_plan(ctx.message.channel.id, plan_type)
        await ctx.send(f'{format_plan_name(plan_content)} started!')

@bot.command()
async def pause(ctx, plan_type: str):
    """Pause a reading plan to temporarily stop receiving daily readings"""
    plan_content, plan = await validate_plan(ctx, plan_type)
    if plan:
        db.update_plan(plan['id'], paused=True)
        await ctx.send(f'{format_plan_name(plan_content)} paused!')

@bot.command()
async def resume(ctx, plan_type: str):
    """Resume a previously paused reading plan"""
    plan_content, plan = await validate_plan(ctx, plan_type)
    if plan:
        db.update_plan(plan['id'], paused=False)
        await ctx.send(f'{format_plan_name(plan_content)} resumed!')

@bot.command()
async def set(ctx, plan_type: str, day: int):
    """Set the current day for a reading plan"""
    plan_content, plan = await validate_plan(ctx, plan_type)
    if plan:
        db.update_plan(plan['id'], current_day=day - 1)
        await ctx.send(f'{format_plan_name(plan_content)} set to day {day}!')

@bot.command()
async def readings(ctx):
    """Get the current reading plan for the channel"""
    plans = db.get_plans_by_channel(ctx.message.channel.id)
    if not plans:
        await ctx.send('No reading plans found!')
        return

    for plan in plans:
        await ctx.send(get_daily_reading(plan))

@bot.command()
async def stop(ctx, plan_type: str):
    """Stop and remove a reading plan from the channel"""
    plan_content, plan = await validate_plan(ctx, plan_type)
    if plan:
        db.delete_plan(plan['id'])
        await ctx.send(f'{format_plan_name(plan_content)} stopped!')

bot.run(os.environ['TOKEN'])
