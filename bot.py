import acronyms
import discord

import yaml
try: from yaml import CLoader as Loader
except ImportError: from yaml import Loader

# load the config
config = dict()
with open('./config.yml') as file:
    yml = yaml.load(file.read(), Loader=Loader)
    try:
        config['token'] = yml['Token']
        config['rating'] = yml['Allow Rating']
        config['verbose'] = yml['Verbose']
    except (KeyError, ValueError): 
        print('Error in config')
        quit(1)
    assert '<TOKEN>' not in repr(config), 'Please add your token to the config!'

# setting up the bot, with its discritpion etc.
intents = discord.Intents.default()
intents.reactions=True
bot = discord.Client(intents=intents) # use Client, as we don't need full bot functionality

@bot.event
async def on_ready():
    print('\n\nBot B00ted\n\n')

# for every message it does these checks
@bot.event
async def on_message(message):
    if message.author.bot: return
    if not message.guild.get_member(bot.user.id).permissions_in(message.channel).send_messages: return
    if config['rating'] and not message.guild.get_member(bot.user.id).permissions_in(message.channel).add_reactions: return
    
    acrs = acronyms.find_most_probable_acrs_in_sentence(message.content)
    if len(acrs) <= 0: return

    acrs_str = ''
    for acr, expanded in acrs.items():
        acrs_str += f'{acr.lower()}: {expanded.title()}\n'
    msg = await message.channel.send(f'Acronyms Found: \n{acrs_str}Was I a good bot? React with ⬆ or ⬇ to vote!')
    
    if config['rating']:
        await msg.add_reaction('⬆')
        await msg.add_reaction('⬇')

@bot.event
async def on_reaction_add(reaction, user): # Don't use raw here, as we want msg to expire
    if not config['rating']: return # must enable ratins in config
    if user.bot: return # reactor must not be a bot
    if reaction.message.author.id != bot.user.id: return # must be on your message

    # Get reaction rating
    rating = reaction.emoji.count('⬆') - reaction.emoji.count('⬇')
    rate(reaction.message, rating)

@bot.event
async def on_raw_reaction_remove(payload):
    if not config['rating']: return # must enable ratins in config
    if bot.get_user(payload.user_id).bot: return # reaction can't be from a bot
    msg = await bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
    if msg.author.id != bot.user.id: return # must be on your message

    rating = str(payload.emoji).count('⬆') - str(payload.emoji).count('⬇')
    rate(msg, -rating) # flip rating
    
def rate(message, rating):
    if rating == 0: return
    # Extract acronyms from message
    if not str(message.content).startswith('Acronyms Found: \n'): return
    lines = message.content.split('\n')[1:-1] # drop first and last info lines
    for line in lines:
        acr, extended = line.split(':')
        acr, extended = acr.lower().strip(), extended.title().strip()
        if config['verbose']: print(f'Acronym {extended} rated {rating}')
        acronyms.rate_acr(extended, rating) # rate them

bot.run(config['token'])