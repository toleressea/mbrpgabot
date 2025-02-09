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

            day = plan["current_day"]
            plan_content = PLANS[plan["plan_id"]]
            message = f'[{plan_content["name"]}]({plan_content["source_link"]}), Daily Reading {day + 1} -- **{", ".join(plan_content["readings"][day])}**'

            await message_channel.send(message)
        await bot.close()

class BibleReadingBotHelp(commands.MinimalHelpCommand):
    async def send_bot_help(self, mapping):
        embed = discord.Embed(
            title="Bible Reading Plan Bot Commands",
            color=discord.Color.blurple()
        )
        
        commands_text = """
• `!start <plan_id>` - Start a new reading plan in the current channel
• `!pause <plan_id>` - Pause the specified reading plan
• `!resume <plan_id>` - Resume a paused reading plan
• `!set <plan_id> <day>` - Set the current day for a reading plan
• `!stop <plan_id>` - Stop and remove a reading plan
• `!plans` - List all active reading plans in this channel
"""
        embed.add_field(name="Available Commands", value=commands_text, inline=False)
        
        plans_text = ""
        for plan_id, plan_data in PLANS.items():
            source_link = f" ([source]({plan_data['source_link']}))" if 'source_link' in plan_data else ""
            plans_text += f"• `{plan_id}` - {plan_data['name']}{source_link}\n"
        
        embed.add_field(name="Available Reading Plans", value=plans_text, inline=False)
        
        channel = self.get_destination()
        await channel.send(embed=embed)

bot.help_command = BibleReadingBotHelp()

# Define various bot commands

@bot.command()
async def plans(ctx):
    """Lists all active reading plans in the current channel"""
    plans = db.get_plans_by_channel(ctx.message.channel.id)

    if plans:
        message = ''
        for p in plans:
            plan_content = PLANS[p["plan_id"]]
            message += f'{plan_content["name"]} (`{p["plan_id"]}`): Current Day - {p["current_day"] + 1}, Paused - {"Yes" if p["paused"] else "No"}\n'

        await ctx.send(message)
    else:
        message = 'No reading plans found. Try adding one with !start <plan_id> from the following list:\n'
        for plan_id, plan_content in PLANS.items():
            message += f'- `{plan_id}` ({plan_content["name"]})\n'
        await ctx.send(message)

@bot.command()
async def start(ctx, plan_id: str):
    """Start a new reading plan in the current channel"""
    plan_id = plan_id.lower()
    if plan_id in PLANS:
        plan_content = PLANS[plan_id]
        channel_id = ctx.message.channel.id

        if db.get_plan_by_channel_and_plan(channel_id, plan_id) is not None:
            await ctx.send(f'{plan_content["name"]} already running in this channel!')
            return

        db.create_plan(channel_id, plan_id)
        await ctx.send(f'{plan_content["name"]} started!')
    else:
        await ctx.send(f'`{plan_id}` is not a supported plan!')

@bot.command()
async def pause(ctx, plan_id: str):
    """Pause a reading plan to temporarily stop receiving daily readings"""
    plan_id = plan_id.lower()
    if plan_id in PLANS:
        plan_content = PLANS[plan_id]
        channel_id = ctx.message.channel.id

        plan = db.get_plan_by_channel_and_plan(channel_id, plan_id)
        if plan:
            db.update_plan(plan['id'], paused=True)
            await ctx.send(f'{plan_content["name"]} paused!')
        else:
            await ctx.send(f'{plan_content["name"]} not running for this channel!')

    else:
        await ctx.send(f'`{plan_id}` is not a supported plan!')

@bot.command()
async def resume(ctx, plan_id: str):
    """Resume a previously paused reading plan"""
    plan_id = plan_id.lower()
    if plan_id in PLANS:
        plan_content = PLANS[plan_id]
        channel_id = ctx.message.channel.id

        plan = db.get_plan_by_channel_and_plan(channel_id, plan_id)
        if plan:
            db.update_plan(plan['id'], paused=False)
            await ctx.send(f'{plan_content["name"]} resumed!')
        else:
            await ctx.send(f'{plan_content["name"]} not running for this channel!')

    else:
        await ctx.send(f'`{plan_id}` is not a supported plan!')

@bot.command()
async def set(ctx, plan_id: str, day: int):
    """Set the current day for a reading plan"""
    plan_id = plan_id.lower()
    if plan_id in PLANS:
        plan_content = PLANS[plan_id]
        channel_id = ctx.message.channel.id

        plan = db.get_plan_by_channel_and_plan(channel_id, plan_id)
        if plan:
            db.update_plan(plan['id'], current_day=day - 1)
            await ctx.send(f'{plan_content["name"]} set to day {day}!')
        else:
            await ctx.send(f'{plan_content["name"]} not running for this channel!')

    else:
        await ctx.send(f'`{plan_id}` is not a supported plan!')

@bot.command()
async def stop(ctx, plan_id: str):
    """Stop and remove a reading plan from the channel"""
    plan_id = plan_id.lower()
    if plan_id in PLANS:
        plan_content = PLANS[plan_id]
        channel_id = ctx.message.channel.id

        plan = db.get_plan_by_channel_and_plan(channel_id, plan_id)
        if plan:
            db.delete_plan(plan['id'])
            await ctx.send(f'{plan_content["name"]} stopped!')
        else:
            await ctx.send(f'{plan_content["name"]} not running for this channel!')

    else:
        await ctx.send(f'`{plan_id}` is not a supported plan!')

bot.run(os.environ['TOKEN'])
