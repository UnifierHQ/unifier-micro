"""
Unifier Micro - A much lighter version of Unifier
Copyright (C) 2024  Green, ItsAsheer

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import nextcord
from nextcord.ext import commands, tasks
import json
import logging
import time
import datetime
from dotenv import load_dotenv
import sys
import os
import re
from utils import log, ui
import math
import tomli
import tomli_w
import traceback

version = '2.0.1'

def timetoint(t,timeoutcap=False):
    try:
        return int(t)
    except:
        pass
    if not type(t) is str:
        t = str(t)
    total = 0
    t = t.replace('mo','n')
    if t.count('n')>1 or t.count('d')>1 or t.count('w')>1 or t.count('h')>1 or t.count('m')>1 or t.count('s')>1:
        raise ValueError('each identifier should never recur')
    t = t.replace('n','n ').replace('d','d ').replace('w','w ').replace('h','h ').replace('m','m ').replace('s','s ')
    times = t.split()
    for part in times:
        if part.endswith('n'):
            multi = int(part[:-1])
            if timeoutcap:
                total += (2419200 * multi)
            else:
                total += (2592000 * multi)
        elif part.endswith('d'):
            multi = int(part[:-1])
            total += (86400 * multi)
        elif part.endswith('w'):
            multi = int(part[:-1])
            total += (604800 * multi)
        elif part.endswith('h'):
            multi = int(part[:-1])
            total += (3600 * multi)
        elif part.endswith('m'):
            multi = int(part[:-1])
            total += (60 * multi)
        elif part.endswith('s'):
            multi = int(part[:-1])
            total += multi
        else:
            raise ValueError('invalid identifier')
    return total

class UnifierMessage:
    def __init__(self, author_id, guild_id, channel_id, original, copies, room):
        self.author_id = author_id
        self.guild_id = guild_id
        self.channel_id = channel_id
        self.id = original
        self.copies = copies
        self.room = room

    def to_dict(self):
        return self.__dict__

    async def fetch_id(self, guild_id):
        if guild_id == self.guild_id:
            return self.id

        return self.copies[guild_id]

class AutoSaveDict(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.file_path = 'data.json'

        # Ensure necessary keys exist
        self.update({'rules': {}, 'rooms': {}, 'restricted': [], 'locked': [],
                     'blocked': {}, 'banned': {}, 'moderators': []})

        # Load data
        self.load_data()

    def load_data(self):
        try:
            with open(self.file_path, 'r') as file:
                data = json.load(file)
            self.update(data)
        except FileNotFoundError:
            pass  # If the file is not found, initialize an empty dictionary

    def save_data(self):
        with open(self.file_path, 'w') as file:
            json.dump(self, file, indent=4)

def is_user_admin(user_id):
    try:
        global admin_ids
        if user_id in admin_ids:
            return True
        else:
            return False
    except:
        return False

def is_room_restricted(room,db):
    try:
        if db['rooms'][room]['meta']['restricted']:
            return True
        else:
            return False
    except:
        return False

def is_room_locked(room,db):
    try:
        if db['rooms'][room]['meta']['locked']:
            return True
        else:
            return False
    except:
        return False

async def fetch_message(message_id):
    for message in messages:
        if str(message.id)==str(message_id) or str(message_id) in str(message.copies):
            return message
    raise ValueError("No message found")

async def convert_1():
    """Converts data structure to be v3.0.0-compatible.
    Eliminates the need for a lot of unneeded keys."""
    if not 'rules' in db.keys():
        # conversion is not needed
        return
    for room in db['rooms']:
        db['rooms'][room] = {'meta':{
            'rules': db['rules'][room],
            'restricted': room in db['restricted'],
            'locked': room in db['locked'],
            'private': False,
            'private_meta': {
                'server': None,
                'allowed': [],
                'invites': [],
                'platform': 'discord'
            },
            'emoji': None,
            'description': None,
            'display_name': None,
            'banned': []
        },'discord': db['rooms'][room]}

    db.pop('rules')
    db.pop('restricted')
    db.pop('locked')

    # not sure what to do about the data stored in rooms_revolt key now...
    # maybe delete the key entirely? or keep it in case conversion went wrong?

    db.save_data()


try:
    with open('.install.json') as file:
        install_info = json.load(file)

    if not install_info['product'] == 'unifier-micro':
        print('This installation is not compatible with Unifier Micro.')
        sys.exit(1)
except:
    if sys.platform == 'win32':
        print('To start the bot, please run "run.bat" instead.')
    else:
        print('To start the bot, please run "./run.sh" instead.')
        print('If you get a "Permission denied" error, run "chmod +x run.sh" and try again.')
    sys.exit(1)

config_file = 'config.toml'
if 'devmode' in sys.argv:
    config_file = 'devconfig.toml'

valid_toml = False
try:
    with open(config_file, 'rb') as file:
        config = tomli.load(file)
    valid_toml = True
except:
    try:
        with open('config.json') as file:
            config = json.load(file)
    except:
        traceback.print_exc()
        print('\nFailed to load config.toml file.\nIf the error is a JSONDecodeError, it\'s most likely a syntax error.')
        sys.exit(1)

    # toml is likely in update files, pull from there
    with open('update/config.toml', 'rb') as file:
        newdata = tomli.load(file)

    def update_toml(old, new):
        for key in new:
            for newkey in new[key]:
                if newkey in old.keys():
                    new[key].update({newkey: old[newkey]})
        return new

    config = update_toml(config, newdata)

    with open(config_file, 'wb+') as file:
        tomli_w.dump(config, file)

try:
    with open('boot_config.json', 'r') as file:
        boot_data = json.load(file)
except:
    boot_data = {}

newdata = {}

for key in config:
    for newkey in config[key]:
        newdata.update({newkey: config[key][newkey]})

data = newdata

env_loaded = load_dotenv()

level = logging.DEBUG if config['debug'] else logging.INFO
package = config['package']
admin_ids = config['admin_ids']

logger = log.buildlogger(package,'core',level)

room_template = {
    'rules': [], 'restricted': False, 'locked': False, 'private': False,
    'private_meta': {
        'server': None,
        'allowed': [],
        'invites': [],
        'platform': 'discord'
    },
    'emoji': None, 'description': None, 'display_name': None, 'banned': []
}

if not '.welcome.txt' in os.listdir():
    x = open('.welcome.txt','w+')
    x.close()
    logger.info('Thank you for installing Unifier Micro!')
    logger.info('Unifier Micro is licensed under the AGPLv3, so if you would like to add your own twist to Unifier Micro, you must follow AGPLv3 conditions.')
    logger.info('You can learn more about modifying Unifier at https://unichat-wiki.pixels.onl//setup-selfhosted/modding-unifier')

if not 'repo' in list(config.keys()):
    logger.critical('WARNING: THIS INSTANCE IS NOT AGPLv3 COMPLAINT!')
    logger.critical('Unifier is licensed under the AGPLv3, meaning you need to make your source code available to users. Please add a repository to the config file under the repo key.')
    sys.exit(1)

if not valid_toml:
    logger.warning('From v3.0.0, Unifier will use config.toml rather than config.json.')
    logger.warning('To change your Unifier configuration, please use the new file.')

if not env_loaded or not "TOKEN" in os.environ:
    logger.critical('Could not find token from .env file! More info: https://unichat-wiki.pixels.onl/setup-selfhosted/getting-started/unifier#set-bot-token')
    sys.exit(1)

if 'token' in list(config.keys()):
    logger.warning('From v1.1.8, Unifier uses .env (dotenv) files to store tokens. We recommend you remove the old token keys from your config.json file.')

db = AutoSaveDict({})
db.load_data()

messages = []

ut_total = round(time.time())
disconnects = 0

# intents = nextcord.Intents(
#     emojis=True,
#     emojis_and_stickers=True,
#     guild_messages=True,
#     guilds=True,
#     message_content=True,
#     messages=True,
#     webhooks=True
# )

intents = nextcord.Intents.all()

mentions = nextcord.AllowedMentions(everyone=False, roles=False, users=False)

bot = commands.Bot(command_prefix=config['prefix'], intents=intents)
bot.remove_command('help')

asciiart = """
  _    _       _  __ _           __  __ _                
 | |  | |     (_)/ _(_)         |  \\/  (_)               
 | |  | |_ __  _| |_ _  ___ _ __| \\  / |_  ___ _ __ ___  
 | |  | | '_ \\| |  _| |/ _ \\ '__| |\\/| | |/ __| '__/ _ \\ 
 | |__| | | | | | | | |  __/ |  | |  | | | (__| | | (_) |
  \\____/|_| |_|_|_| |_|\\___|_|  |_|  |_|_|\\___|_|  \\___/ 
"""

print(asciiart)
print(f'Version: {version}')
print()

@tasks.loop(seconds=round(config['ping']))
async def periodicping():
    guild = bot.guilds[0]
    try:
        await bot.fetch_channel(guild.text_channels[0].id)
    except:
        pass

@bot.event
async def on_ready():
    if not periodicping.is_running() and config['ping'] > 0:
        periodicping.start()
        logger.debug(f'Pinging servers every {round(config["ping"])} seconds')
    elif config['ping'] <= 0:
        logger.debug(f'Periodic pinging disabled')
    logger.info('Unifier is ready!')

@bot.event
async def on_disconnect():
    global disconnects
    disconnects += 1

@bot.command(description='Shows this command.')
async def help(ctx):
    show_sysmgr = False
    show_admin = False
    show_moderation = False

    admin_restricted = [
        'addmod','delmod','make','roomdesc','roomlock','roomrestrict','addrule','delrule'
    ]

    mod_restricted = [
        'globalban','globalunban','warn','delwarn','delban'
    ]

    if ctx.author.id == config['owner']:
        show_sysmgr = True
        show_admin = True
        show_moderation = True
    elif ctx.author.id in config['admin_ids']:
        show_admin = True
        show_moderation = True
    elif ctx.author.id in db['moderators']:
        show_moderation = True

    panel = 1
    limit = 20
    page = 0
    match = 0
    namematch = False
    descmatch = False
    cogname = 'all'
    cmdname = ''
    query = ''
    msg = None
    interaction = None

    while True:
        embed = nextcord.Embed(color=0xed4545)
        maxpage = 0
        components = ui.MessageComponents()

        if panel==1:
            cmds = list(bot.commands)

            offset = 0

            def search_filter(query, query_cmd):
                if match==0:
                    return (
                        query.lower() in query_cmd.qualified_name and namematch or
                        query.lower() in query_cmd.description.lower() and descmatch
                    )
                elif match==1:
                    return (
                        ((query.lower() in query_cmd.qualified_name and namematch) or not namematch) and
                        ((query.lower() in query_cmd.description.lower() and descmatch) or not descmatch)
                    )

            for index in range(len(cmds)):
                cmd = cmds[index-offset]
                if (
                        cmd.hidden or cmd.qualified_name in admin_restricted and not show_admin or
                        cmd.qualified_name in mod_restricted and not show_moderation
                ) and not show_sysmgr or (
                        cogname=='search' and not search_filter(query,cmd)
                ):
                    cmds.pop(index-offset)
                    offset += 1

            embed.title = (
                f'{bot.user.global_name or bot.user.name} help / search' if cogname == 'search' else
                f'{bot.user.global_name or bot.user.name} help'
            )
            embed.description = 'Choose a command to view its info!'

            if len(cmds)==0:
                maxpage = 0
                embed.add_field(
                    name='No commands',
                    value=(
                        'There are no commands matching your search query.' if cogname=='search' else
                        'There are no commands in this extension.'
                    ),
                    inline=False
                )
                selection = nextcord.ui.StringSelect(
                    max_values=1, min_values=1, custom_id='selection', placeholder='Command...',disabled=True
                )
                selection.add_option(
                    label='No commands'
                )
            else:
                maxpage = math.ceil(len(cmds) / limit) - 1
                selection = nextcord.ui.StringSelect(
                    max_values=1, min_values=1, custom_id='selection', placeholder='Command...'
                )

                cmds = await bot.loop.run_in_executor(
                    None,lambda: sorted(
                        cmds,
                        key=lambda x: x.qualified_name.lower()
                    )
                )

                for x in range(limit):
                    index = (page * limit) + x
                    if index >= len(cmds):
                        break
                    cmd = cmds[index]
                    embed.add_field(
                        name=f'`{cmd.qualified_name}`',
                        value=cmd.description if cmd.description else 'No description provided',
                        inline=False
                    )
                    selection.add_option(
                        label=cmd.qualified_name,
                        description=(cmd.description if len(
                            cmd.description
                        ) <= 100 else cmd.description[:-(len(cmd.description) - 97)] + '...'
                                     ) if cmd.description else 'No description provided',
                        value=cmd.qualified_name
                    )

            if cogname=='search':
                embed.description = f'Searching: {query} (**{len(cmds)}** results)'
                maxcount = (page+1)*limit
                if maxcount > len(cmds):
                    maxcount = len(cmds)
                embed.set_footer(
                    text=f'Page {page + 1} of {maxpage + 1} | {page*limit+1}-{maxcount} of {len(cmds)} results'
                )

            components.add_row(
                ui.ActionRow(
                    selection
                )
            )

            components.add_row(
                ui.ActionRow(
                    nextcord.ui.Button(
                        style=nextcord.ButtonStyle.blurple,
                        label='Previous',
                        custom_id='prev',
                        disabled=page <= 0
                    ),
                    nextcord.ui.Button(
                        style=nextcord.ButtonStyle.blurple,
                        label='Next',
                        custom_id='next',
                        disabled=page >= maxpage
                    ),
                    nextcord.ui.Button(
                        style=nextcord.ButtonStyle.green,
                        label='Search',
                        custom_id='search',
                        emoji='\U0001F50D'
                    )
                )
            )
            if cogname=='search':
                components.add_row(
                    ui.ActionRow(
                        nextcord.ui.Button(
                            custom_id='match',
                            label=(
                                'Matches any of' if match==0 else
                                'Matches both'
                            ),
                            style=(
                                nextcord.ButtonStyle.green if match==0 else
                                nextcord.ButtonStyle.blurple
                            ),
                            emoji=(
                                '\U00002194' if match==0 else
                                '\U000023FA'
                            )
                        ),
                        nextcord.ui.Button(
                            custom_id='name',
                            label='Command name',
                            style=nextcord.ButtonStyle.green if namematch else nextcord.ButtonStyle.gray
                        ),
                        nextcord.ui.Button(
                            custom_id='desc',
                            label='Command description',
                            style=nextcord.ButtonStyle.green if descmatch else nextcord.ButtonStyle.gray
                        )
                    )
                )
            if cogname=='search':
                components.add_row(
                    ui.ActionRow(
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.gray,
                            label='Back',
                            custom_id='back',
                        )
                    )
                )
        elif panel==2:
            cmd = bot.get_command(cmdname)
            embed.title = (
                f'{bot.user.global_name or bot.user.name} help / search / {cmdname}' if cogname=='search' else
                f'{bot.user.global_name or bot.user.name} help / {cmdname}'
            )
            embed.description =(
                f'# **`{bot.command_prefix}{cmdname}`**\n{cmd.description if cmd.description else "No description provided"}'
            )
            if len(cmd.aliases) > 0:
                aliases = []
                for alias in cmd.aliases:
                    aliases.append(f'`{bot.command_prefix}{alias}`')
                embed.add_field(
                    name='Aliases',value='\n'.join(aliases) if len(aliases) > 1 else aliases[0],inline=False
                )
            embed.add_field(name='Usage', value=(
                f'`{bot.command_prefix}{cmdname} {cmd.signature}`' if len(cmd.signature) > 0 else f'`{bot.command_prefix}{cmdname}`'), inline=False
            )
            components.add_rows(
                ui.ActionRow(
                    nextcord.ui.Button(
                        style=nextcord.ButtonStyle.gray,
                        label='Back',
                        custom_id='back',
                    )
                )
            )

        if not cogname=='search' and panel==1:
            embed.set_footer(text=f'Page {page+1} of {maxpage+1}')
        if not msg:
            msg = await ctx.send(embed=embed,view=components,reference=ctx.message,mention_author=False)
        else:
            if not interaction.response.is_done():
                await interaction.response.edit_message(embed=embed,view=components)
        embed.clear_fields()

        def check(interaction):
            return interaction.user.id==ctx.author.id and interaction.message.id==msg.id

        try:
            interaction = await bot.wait_for('interaction',check=check,timeout=60)
        except:
            await msg.edit(view=None)
            break
        if interaction.type==nextcord.InteractionType.component:
            if interaction.data['custom_id']=='selection':
                if panel==0:
                    cogname = interaction.data['values'][0]
                elif panel==1:
                    cmdname = interaction.data['values'][0]
                if cogname=='all':
                    cogname = ''
                panel += 1
                page = 0
            elif interaction.data['custom_id'] == 'back':
                panel -= 1
                if panel < 1:
                    panel = 1
                    cogname = 'all'
                page = 0
            elif interaction.data['custom_id'] == 'prev':
                page -= 1
            elif interaction.data['custom_id'] == 'next':
                page += 1
            elif interaction.data['custom_id'] == 'search':
                modal = nextcord.ui.Modal(title='Search...',auto_defer=False)
                modal.add_item(
                    nextcord.ui.TextInput(
                        label='Search query',
                        style=nextcord.TextInputStyle.short,
                        placeholder='Type a command...'
                    )
                )
                await interaction.response.send_modal(modal)
            elif interaction.data['custom_id'] == 'match':
                match += 1
                if match > 1:
                    match = 0
            elif interaction.data['custom_id'] == 'name':
                namematch = not namematch
                if not namematch and not descmatch:
                    namematch = True
            elif interaction.data['custom_id'] == 'desc':
                descmatch = not descmatch
                if not namematch and not descmatch:
                    descmatch = True
        elif interaction.type==nextcord.InteractionType.modal_submit:
            panel = 1
            cogname = 'search'
            query = interaction.data['components'][0]['components'][0]['value']
            namematch = True
            descmatch = True
            match = 0

@bot.command(description='Shows bot uptime.')
async def uptime(ctx):
    embed = nextcord.Embed(
        title=f'{bot.user.global_name or bot.user.name} uptime',
        description=f'The bot has been up since <t:{ut_total}:f>.'
    )
    t = round(time.time()) - ut_total
    td = datetime.timedelta(seconds=t)
    d = td.days
    h, m, s = str(td).split(',')[len(str(td).split(','))-1].split(':')
    embed.add_field(
        name='Total uptime',
        value=f'`{d}` days, `{int(h)}` hours, `{int(m)}` minutes, `{int(s)}` seconds',
        inline=False
    )
    embed.add_field(
        name='Disconnects/hr',
        value=f'{round(disconnects / (t / 3600), 2)}',
        inline=False
    )
    await ctx.send(embed=embed)

@bot.command(hidden=True,description='Adds a moderator to the instance.')
async def addmod(ctx,*,userid):
    if not is_user_admin(ctx.author.id):
        return await ctx.send('Only admins can manage moderators!')
    try:
        userid = int(userid)
    except:
        try:
            userid = int(userid.replace('<@','',1).replace('!','',1).replace('>','',1))
        except:
            return await ctx.send('Not a valid user!')
    try:
        user = await bot.fetch_user(userid)
    except:
        return await ctx.send('Not a valid user!')
    if userid in db['moderators']:
        return await ctx.send('This user is already a moderator!')
    if is_user_admin(userid) or user.bot:
        return await ctx.send('are you fr')
    db['moderators'].append(userid)
    db.save_data()
    mod = f'{user.name}#{user.discriminator}'
    if user.discriminator=='0':
        mod = f'@{user.name}'
    await ctx.send(f'**{mod}** is now a moderator!')

@bot.command(hidden=True,aliases=['remmod','delmod'],description='Removes a moderator from the instance.')
async def removemod(ctx,*,userid):
    if not is_user_admin(ctx.author.id):
        return await ctx.send('Only admins can manage moderators!')
    try:
        userid = int(userid)
    except:
        try:
            userid = int(userid.replace('<@','',1).replace('!','',1).replace('>','',1))
        except:
            return await ctx.send('Not a valid user!')
    try:
        user = await bot.fetch_user(userid)
    except:
        return await ctx.send('Not a valid user!')
    if not userid in db['moderators']:
        return await ctx.send('This user is not a moderator!')
    if is_user_admin(userid):
        return await ctx.send('are you fr')
    db['moderators'].remove(userid)
    db.save_data()
    mod = f'{user.name}#{user.discriminator}'
    if user.discriminator=='0':
        mod = f'@{user.name}'
    await ctx.send(f'**{mod}** is no longer a moderator!')

@bot.command(hidden=True, aliases=['newroom'])
async def make(ctx,*,room):
    if not is_user_admin(ctx.author.id):
        return await ctx.send('Only admins can create rooms!')
    room = room.lower()
    if not bool(re.match("^[A-Za-z0-9_-]*$",room)):
        return await ctx.send('Room names may only contain alphabets, numbers, dashes, and underscores.')
    if room in list(db['rooms'].keys()):
        return await ctx.send('This room already exists!')
    db['rooms'].update({room:dict(room_template)})
    db.save_data()
    await ctx.send(f'Created room `{room}`!')

@bot.command(hidden=True,description="Adds a given rule to a given room.")
async def addrule(ctx,room,*,rule):
    if not is_user_admin(ctx.author.id):
        return await ctx.send('Only admins can modify rules!')
    room = room.lower()
    if not room in list(db['rooms'].keys()):
        return await ctx.send('This room does not exist!')
    if len(db['rooms'][room]['meta']['rules']) >= 25:
        return await ctx.send('You can only have up to 25 rules in a room!')
    db['rules'][room]['rules'].append(rule)
    db.save_data()
    await ctx.send('Added rule!')

@bot.command(hidden=True,description="Removes a given rule from a given room.")
async def delrule(ctx,room,*,rule):
    if not is_user_admin(ctx.author.id):
        return await ctx.send('Only admins can modify rules!')
    room = room.lower()
    try:
        rule = int(rule)
        if rule <= 0:
            raise ValueError()
    except:
        return await ctx.send('Rule must be a number higher than 0.')
    if not room in list(db['rooms'].keys()):
        return await ctx.send('This room does not exist!')
    db['rooms'][room]['meta']['rules'].pop(rule-1)
    db.save_data()
    await ctx.send('Removed rule!')


@bot.command(description='Displays room rules for the specified room.')
async def rules(ctx, *, room=''):
    """Displays room rules for the specified room."""
    if is_room_restricted(room, db) and not is_user_admin(ctx.author.id):
        return await ctx.send(':eyes:')
    room = room.lower()
    if room == '' or not room:
        room = 'main'

    if not room in list(db['rooms'].keys()):
        return await ctx.send(f'This room doesn\'t exist! Run `{bot.command_prefix}rooms` to get a full list.')

    index = 0
    text = ''
    rules = db['rooms'][room]['meta']['rules']
    if len(rules) == 0:
        return await ctx.send('The room creator hasn\'t added rules yet. For now, follow `main` room rules.')
    for rule in rules:
        if text == '':
            text = f'1. {rule}'
        else:
            text = f'{text}\n{index}. {rule}'
        index += 1
    embed = nextcord.Embed(title='Room rules', description=text)
    embed.set_footer(text='Failure to follow room rules may result in user or server restrictions.')
    await ctx.send(embed=embed)

@bot.command(
    hidden=True,
    description='Restricts/unrestricts room. Only admins will be able to collect to this room when restricted.'
)
async def restrict(ctx,*,room):
    if not is_user_admin(ctx.author.id):
        return await ctx.send('Only admins can modify rooms!')
    room = room.lower()
    if not room in list(db['rooms'].keys()):
        return await ctx.send('This room does not exist!')
    if db['rooms'][room]['meta']['restricted']:
        db['rooms'][room]['meta']['restricted'] = False
        await ctx.send(f'Unrestricted `{room}`!')
    else:
        db['rooms'][room]['meta']['restricted'] = True
        await ctx.send(f'Restricted `{room}`!')
    db.save_data()

@bot.command(
    hidden=True,
    description='Locks/unlocks a room. Only moderators and admins will be able to chat in this room when locked.'
)
async def lock(ctx,*,room):
    if not is_user_admin(ctx.author.id):
        return await ctx.send('Only admins can modify rooms!')
    room = room.lower()
    if not room in list(db['rooms'].keys()):
        return await ctx.send('This room does not exist!')
    if db['rooms'][room]['meta']['locked']:
        db['rooms'][room]['meta']['locked'] = False
        await ctx.send(f'Unlocked `{room}`!')
    else:
        db['rooms'][room]['meta']['locked'] = True
        await ctx.send(f'Locked `{room}`!')
    db.save_data()

@bot.command(name='display-name', hidden=True, description='Sets room display name.')
async def display_name(ctx, room, *, name=''):
    if not is_user_admin(ctx.author.id):
        return await ctx.send('Only admins can modify rooms!')
    room = room.lower()
    if not room in list(db['rooms'].keys()):
        return await ctx.send('This room does not exist!')

    if len(name) == 0:
        if not db['rooms'][room]['meta']['display_name']:
            return await ctx.send('There is no display name to reset for this room.')
        db['rooms'][room]['meta']['display_name'] = None
        db.save_data()
        return await ctx.send('Display name removed.')
    elif len(name) > 32:
        return await ctx.send('Display name is too long. Please keep it within 32 characters.')
    db['rooms'][room]['meta']['display_name'] = name
    db.save_data()
    await ctx.send(f'Updated display name to `{name}`!')

@bot.command(description='Measures bot latency.')
async def ping(ctx):
    t = time.time()
    msg = await ctx.send('Ping!')
    diff = round((time.time() - t) * 1000, 1)
    text = 'Pong! :ping_pong:'
    if diff <= 300 and bot.latency <= 0.2:
        embed = nextcord.Embed(title='Normal - all is well!',
                               description=f'Roundtrip: {diff}ms\nHeartbeat: {round(bot.latency * 1000, 1)}ms\n\nAll is working normally!',
                               color=0x00ff00)
    elif diff <= 600 and bot.latency <= 0.5:
        embed = nextcord.Embed(title='Fair - could be better.',
                               description=f'Roundtrip: {diff}ms\nHeartbeat: {round(bot.latency * 1000, 1)}ms\n\nNothing\'s wrong, but the latency could be better.',
                               color=0xffff00)
    elif diff <= 2000 and bot.latency <= 1.0:
        embed = nextcord.Embed(title='SLOW - __**oh no.**__',
                               description=f'Roundtrip: {diff}ms\nHeartbeat: {round(bot.latency * 1000, 1)}ms\n\nBot latency is higher than normal, messages may be slow to arrive.',
                               color=0xff0000)
    else:
        text = 'what'
        embed = nextcord.Embed(title='**WAY TOO SLOW**',
                               description=f'Roundtrip: {diff}ms\nHeartbeat: {round(bot.latency * 1000, 1)}ms\n\nSomething is DEFINITELY WRONG here. Consider checking [Discord status](https://discordstatus.com) page.',
                               color=0xbb00ff)
    await msg.edit(content=text, embed=embed)

@bot.command(description='Shows a list of rooms.')
async def rooms(ctx):
    show_restricted = False
    show_locked = False

    if ctx.author.id in config['admin_ids']:
        show_restricted = True
        show_locked = True
    elif ctx.author.id in db['moderators']:
        show_locked = True

    panel = 0
    limit = 8
    page = 0
    match = 0
    namematch = False
    descmatch = False
    was_searching = False
    roomname = ''
    query = ''
    msg = None
    interaction = None

    while True:
        embed = nextcord.Embed(color=0xed4545)
        maxpage = 0
        components = ui.MessageComponents()

        if panel == 0:
            was_searching = False
            roomlist = list(db['rooms'].keys())
            offset = 0
            for x in range(len(roomlist)):
                if (not show_restricted and is_room_restricted(roomlist[x-offset],db) or
                        not show_locked and is_room_locked(roomlist[x-offset],db)):
                    roomlist.pop(x-offset)
                    offset += 1

            maxpage = math.ceil(len(roomlist) / limit) - 1
            if interaction:
                if page > maxpage:
                    page = maxpage
            embed.title = f'{bot.user.global_name or bot.user.name} rooms'
            embed.description = 'Choose a room to view its info!'
            selection = nextcord.ui.StringSelect(
                max_values=1, min_values=1, custom_id='selection', placeholder='Room...'
            )

            for x in range(limit):
                index = (page * limit) + x
                if index >= len(roomlist):
                    break
                name = roomlist[index]
                display_name = (
                    db['rooms'][name]['meta']['display_name'] or name
                )
                emoji = (
                    '\U0001F527' if is_room_restricted(roomlist[index],db) else
                    '\U0001F512' if is_room_locked(roomlist[index],db) else
                    '\U0001F310'
                )
                description = (
                    'Restricted room' if is_room_restricted(roomlist[index],db) else
                    'Locked room' if is_room_locked(roomlist[index],db) else
                    'Public room'
                )

                embed.add_field(
                    name=f'{emoji} '+(
                        f'{display_name} (`{name}`)' if db['rooms'][name]['meta']['display_name'] else
                        f'`{display_name}`'
                    ),
                    value=description,
                    inline=False
                )
                selection.add_option(
                    label=display_name,
                    emoji=emoji,
                    description=description,
                    value=name
                )

            if len(embed.fields) == 0:
                embed.add_field(
                    name='No rooms',
                    value='There\'s no rooms here!',
                    inline=False
                )
                selection.add_option(
                    label='placeholder',
                    value='placeholder'
                )
                selection.disabled = True

            components.add_rows(
                ui.ActionRow(
                    selection
                ),
                ui.ActionRow(
                    nextcord.ui.Button(
                        style=nextcord.ButtonStyle.blurple,
                        label='Previous',
                        custom_id='prev',
                        disabled=page <= 0 or selection.disabled
                    ),
                    nextcord.ui.Button(
                        style=nextcord.ButtonStyle.blurple,
                        label='Next',
                        custom_id='next',
                        disabled=page >= maxpage or selection.disabled
                    ),
                    nextcord.ui.Button(
                        style=nextcord.ButtonStyle.green,
                        label='Search',
                        custom_id='search',
                        emoji='\U0001F50D',
                        disabled=selection.disabled
                    )
                )
            )
        elif panel == 1:
            was_searching = True
            roomlist = list(db['rooms'].keys())

            def search_filter(query, query_cmd):
                return query.lower() in query_cmd.lower()

            offset = 0
            for x in range(len(roomlist)):
                room = roomlist[x - offset]
                if (
                        not show_restricted and is_room_restricted(roomlist[x - offset], db) or
                        not show_locked and is_room_locked(roomlist[x - offset], db)
                ) and not show_restricted or not search_filter(query,room):
                    roomlist.pop(x - offset)
                    offset += 1

            embed.title = f'{bot.user.global_name or bot.user.name} rooms / search'
            embed.description = 'Choose a room to view its info!'

            if len(roomlist) == 0:
                maxpage = 0
                embed.add_field(
                    name='No rooms',
                    value='There are no rooms matching your search query.',
                    inline=False
                )
                selection = nextcord.ui.StringSelect(
                    max_values=1, min_values=1, custom_id='selection', placeholder='Room...', disabled=True
                )
                selection.add_option(
                    label='No rooms'
                )
            else:
                maxpage = math.ceil(len(roomlist) / limit) - 1
                selection = nextcord.ui.StringSelect(
                    max_values=1, min_values=1, custom_id='selection', placeholder='Room...'
                )

                roomlist = await bot.loop.run_in_executor(None, lambda: sorted(
                    roomlist,
                    key=lambda x: x.lower()
                ))

                for x in range(limit):
                    index = (page * limit) + x
                    if index >= len(roomlist):
                        break
                    room = roomlist[index]
                    display_name = (
                        db['rooms'][room]['meta']['display_name'] or room
                    )
                    emoji = (
                        '\U0001F527' if is_room_restricted(roomlist[index], db) else
                        '\U0001F512' if is_room_locked(roomlist[index], db) else
                        '\U0001F310'
                    )
                    roomdesc = (
                        'Restricted room' if is_room_restricted(roomlist[index], db) else
                        'Locked room' if is_room_locked(roomlist[index], db) else
                        'Public room'
                    )
                    embed.add_field(
                        name=f'{emoji} '+(
                            f'{display_name} (`{room}`)' if db['rooms'][room]['meta']['display_name'] else
                            f'`{display_name}`'
                        ),
                        value=roomdesc,
                        inline=False
                    )
                    selection.add_option(
                        label=display_name,
                        description=roomdesc if len(roomdesc) <= 100 else roomdesc[:-(len(roomdesc) - 97)] + '...',
                        value=room,
                        emoji=emoji
                    )

            embed.description = f'Searching: {query} (**{len(roomlist)}** results)'
            maxcount = (page + 1) * limit
            if maxcount > len(roomlist):
                maxcount = len(roomlist)
            embed.set_footer(
                text=(
                    f'Page {page + 1} of {maxpage + 1} | {page * limit + 1}-{maxcount} of {len(roomlist)}'+
                    ' results'
                )
            )

            components.add_row(
                ui.ActionRow(
                    selection
                )
            )

            components.add_row(
                ui.ActionRow(
                    nextcord.ui.Button(
                        style=nextcord.ButtonStyle.blurple,
                        label='Previous',
                        custom_id='prev',
                        disabled=page <= 0
                    ),
                    nextcord.ui.Button(
                        style=nextcord.ButtonStyle.blurple,
                        label='Next',
                        custom_id='next',
                        disabled=page >= maxpage
                    ),
                    nextcord.ui.Button(
                        style=nextcord.ButtonStyle.green,
                        label='Search',
                        custom_id='search',
                        emoji='\U0001F50D'
                    )
                )
            )
            components.add_row(
                ui.ActionRow(
                    nextcord.ui.Button(
                        custom_id='match',
                        label=(
                            'Matches any of' if match == 0 else
                            'Matches both'
                        ),
                        style=(
                            nextcord.ButtonStyle.green if match == 0 else
                            nextcord.ButtonStyle.blurple
                        ),
                        emoji=(
                            '\U00002194' if match == 0 else
                            '\U000023FA'
                        )
                    ),
                    nextcord.ui.Button(
                        custom_id='name',
                        label='Room name',
                        style=nextcord.ButtonStyle.green if namematch else nextcord.ButtonStyle.gray
                    ),
                    nextcord.ui.Button(
                        custom_id='desc',
                        label='Room description',
                        style=nextcord.ButtonStyle.green if descmatch else nextcord.ButtonStyle.gray
                    )
                )
            )
            components.add_row(
                ui.ActionRow(
                    nextcord.ui.Button(
                        style=nextcord.ButtonStyle.gray,
                        label='Back',
                        custom_id='back',
                    )
                )
            )
        elif panel == 2:
            embed.title = (
                f'{bot.user.global_name or bot.user.name} rooms / search / {roomname}'
                if was_searching else
                f'{bot.user.global_name or bot.user.name} rooms / {roomname}'
            )
            display_name = (
                db['rooms'][roomname]['meta']['display_name'] or roomname
            )
            description = (
                db['descriptions'][roomname]
                if roomname in db['descriptions'].keys() else 'This room has no description.'
            )
            emoji = (
                '\U0001F527' if is_room_restricted(roomname, db) else
                '\U0001F512' if is_room_locked(roomname, db) else
                '\U0001F310'
            )
            if db['rooms'][roomname]['meta']['display_name']:
                embed.description = f'# **{emoji} {display_name}**\n`{roomname}`\n\n{description}'
            else:
                embed.description = f'# **{emoji} `{display_name}`**\n{description}'
            components.add_rows(
                ui.ActionRow(
                    nextcord.ui.Button(
                        style=nextcord.ButtonStyle.blurple,
                        label='View room rules',
                        custom_id='rules',
                    )
                ),
                ui.ActionRow(
                    nextcord.ui.Button(
                        style=nextcord.ButtonStyle.gray,
                        label='Back',
                        custom_id='back',
                    )
                )
            )
        elif panel==3:
            embed.title = (
                f'{bot.user.global_name or bot.user.name} rooms / search / {roomname} / rules'
                if was_searching else
                f'{bot.user.global_name or bot.user.name} rooms / {roomname} / rules'
            )
            index = 0
            text = ''
            rules = db['rooms'][roomname]['rules']
            for rule in rules:
                if text == '':
                    text = f'1. {rule}'
                else:
                    text = f'{text}\n{index}. {rule}'
                index += 1
            if len(rules)==0:
                text = (
                    'The room admins haven\'t added rules for this room yet.\n'+
                    'Though, do remember to use common sense and refrain from doing things that you shouldn\'t do.'
                )
            embed.description=text
            components.add_rows(
                ui.ActionRow(
                    nextcord.ui.Button(
                        style=nextcord.ButtonStyle.gray,
                        label='Back',
                        custom_id='back',
                    )
                )
            )

        if panel == 0:
            embed.set_footer(text=f'Page {page + 1} of {maxpage + 1}')
        if not msg:
            msg = await ctx.send(embed=embed, view=components, reference=ctx.message, mention_author=False)
        else:
            if not interaction.response.is_done():
                await interaction.response.edit_message(embed=embed, view=components)
        embed.clear_fields()

        def check(interaction):
            return interaction.user.id == ctx.author.id and interaction.message.id == msg.id

        try:
            interaction = await bot.wait_for('interaction', check=check, timeout=60)
        except:
            await msg.edit(view=None)
            break
        if interaction.type == nextcord.InteractionType.component:
            if interaction.data['custom_id'] == 'selection':
                roomname = interaction.data['values'][0]
                panel = 2
                page = 0
            elif interaction.data['custom_id'] == 'back':
                panel -= 1
                if panel < 0 or panel==1 and not was_searching:
                    panel = 0
                page = 0
            elif interaction.data['custom_id'] == 'rules':
                panel += 1
            elif interaction.data['custom_id'] == 'prev':
                page -= 1
            elif interaction.data['custom_id'] == 'next':
                page += 1
            elif interaction.data['custom_id'] == 'search':
                modal = nextcord.ui.Modal(title='Search...', auto_defer=False)
                modal.add_item(
                    nextcord.ui.TextInput(
                        label='Search query',
                        style=nextcord.TextInputStyle.short,
                        placeholder='Type something...'
                    )
                )
                await interaction.response.send_modal(modal)
            elif interaction.data['custom_id'] == 'match':
                match += 1
                if match > 1:
                    match = 0
            elif interaction.data['custom_id'] == 'name':
                namematch = not namematch
                if not namematch and not descmatch:
                    namematch = True
            elif interaction.data['custom_id'] == 'desc':
                descmatch = not descmatch
                if not namematch and not descmatch:
                    descmatch = True
        elif interaction.type == nextcord.InteractionType.modal_submit:
            panel = 1
            query = interaction.data['components'][0]['components'][0]['value']
            namematch = True
            descmatch = True
            match = 0

@bot.command(aliases=['guilds'],description='Lists all servers connected to a given room.')
async def servers(ctx,*,room='main'):
    try:
        data = db['rooms'][room]
    except:
        return await ctx.send(f'This isn\'t a valid room. Run `{bot.command_prefix}rooms` for a list of all rooms.')
    text = ''
    for guild_id in data:
        try:
            name = bot.get_guild(int(guild_id)).name
        except:
            continue
        if len(text)==0:
            text = f'- {name} (`{guild_id}`)'
        else:
            text = f'{text}\n- {name} (`{guild_id}`)'
    embed = nextcord.Embed(title=f'Servers connected to `{room}`',description=text)
    await ctx.send(embed=embed)

@bot.command(aliases=['link','connect','federate','bridge'],description='Connects the channel to a given room.')
async def bind(ctx, *, room=''):
    if not ctx.author.guild_permissions.manage_channels and not is_user_admin(ctx.author.id):
        return await ctx.send('You don\'t have the necessary permissions.')
    if is_room_restricted(room, db) and not is_user_admin(ctx.author.id):
        return await ctx.send('Only admins can bind channels to restricted rooms.')
    room = room.lower()
    if room == '' or not room:  # Added "not room" as a failback
        room = 'main'
        await ctx.send('**No room was given, defaulting to main**')
    try:
        data = db['rooms'][room]
    except:
        return await ctx.send(f'This isn\'t a valid room. Run `{bot.command_prefix}rooms` for a list of rooms.')
    embed = nextcord.Embed(title='Ensuring channel is not connected...', description='This may take a while.')
    msg = await ctx.send(embed=embed)
    for roomname in list(db['rooms'].keys()):
        # Prevent duplicate binding
        try:
            hook_id = db['rooms'][roomname][f'{ctx.guild.id}'][0]
            hook = await bot.fetch_webhook(hook_id)
            if hook.channel_id == ctx.channel.id:
                embed.title = 'Channel already linked!'
                embed.colour = 0xff0000
                embed.description = f'This channel is already linked to `{roomname}`!\nRun `{bot.command_prefix}unbind {roomname}` to unbind from it.'
                return await msg.edit(embed=embed)
        except:
            continue
    try:
        try:
            guild = data[f'{ctx.guild.id}']
        except:
            guild = []
        if len(guild) >= 1:
            return await ctx.send(
                f'Your server is already linked to this room.\n**Accidentally deleted the webhook?** `{bot.command_prefix}unlink` it then `{bot.command_prefix}link` it back.')
        index = 0
        text = ''
        if len(db['rooms'][room]['meta']['rules']) == 0:
            text = f'No rules exist yet for this room! For now, follow the main room\'s rules.\nYou can always view rules if any get added using `{bot.command_prefix}rules {room}`.'
        else:
            for rule in db['rooms'][room]['meta']['rules']:
                if text == '':
                    text = f'1. {rule}'
                else:
                    text = f'{text}\n{index}. {rule}'
                index += 1
        text = f'{text}\n\nPlease display these rules somewhere accessible.'
        embed = nextcord.Embed(title='Please agree to the room rules first:', description=text)
        embed.set_footer(text='Failure to follow room rules may result in user or server restrictions.')
        row = [
            nextcord.ui.Button(
                style=nextcord.ButtonStyle.green, label='Accept and bind', custom_id=f'accept', disabled=False
            ),
            nextcord.ui.Button(
                style=nextcord.ButtonStyle.red, label='No thanks', custom_id=f'reject', disabled=False
            )
        ]
        btns = ui.ActionRow(row[0], row[1])
        components = ui.MessageComponents()
        components.add_row(btns)
        await msg.edit(embed=embed, view=components)

        def check(interaction):
            return interaction.user.id == ctx.author.id and (
                    interaction.data['custom_id'] == 'accept' or
                    interaction.data['custom_id'] == 'reject'
            ) and interaction.channel.id == ctx.channel.id

        try:
            resp = await bot.wait_for("interaction", check=check, timeout=60.0)
        except:
            row[0].disabled = True
            row[1].disabled = True
            btns = ui.ActionRow(row[0], row[1])
            components = ui.MessageComponents()
            components.add_row(btns)
            await msg.edit(view=components)
            return await ctx.send('Timed out.')
        row[0].disabled = True
        row[1].disabled = True
        btns = ui.ActionRow(row[0], row[1])
        components = ui.MessageComponents()
        components.add_row(btns)
        await resp.response.edit_message(view=components)
        if resp.data['custom_id'] == 'reject':
            return
        webhook = await ctx.channel.create_webhook(name='Unifier Bridge')
        data = db['rooms'][room]
        guild = [webhook.id]
        data.update({f'{ctx.guild.id}': guild})
        db['rooms'][room] = data
        db.save_data()
        await ctx.send(
            '# :white_check_mark: Linked channel to Unifier network!\nYou can now send messages to the Unifier network through this channel. Say hi!')
        try:
            await msg.pin()
        except:
            pass
    except:
        await ctx.send('Something went wrong - check my permissions.')
        raise

@bot.command(aliases=['unlink','disconnect'],description='Disconnects the server from a given room.')
async def unbind(ctx, *, room=''):
    if room == '':
        return await ctx.send('You must specify the room to unbind from.')
    if not ctx.author.guild_permissions.manage_channels and not is_user_admin(ctx.author.id):
        return await ctx.send('You don\'t have the necessary permissions.')
    room = room.lower()
    try:
        data = db['rooms'][room]
    except:
        return await ctx.send('This isn\'t a valid room. Try `main`, `pr`, `prcomments`, or `liveries` instead.')
    try:
        try:
            hooks = await ctx.guild.webhooks()
        except:
            return await ctx.send('I cannot manage webhooks.')
        if f'{ctx.guild.id}' in list(data.keys()):
            hook_ids = data[f'{ctx.guild.id}']
        else:
            hook_ids = []
        for webhook in hooks:
            if webhook.id in hook_ids:
                await webhook.delete()
                break
        data.pop(f'{ctx.guild.id}')
        db['rooms'][room] = data
        db.save_data()
        await ctx.send(
            '# :white_check_mark: Unlinked channel from Unifier network!\nThis channel is no longer linked, nothing from now will be bridged.')
    except:
        await ctx.send('Something went wrong - check my permissions.')
        raise

@bot.command(description='Blocks a user or server from bridging messages to your server.')
async def block(ctx, *, target):
    if not (ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.kick_members or
            ctx.author.guild_permissions.ban_members):
        return await ctx.send('You cannot restrict members/servers.')
    try:
        userid = int(target.replace('<@', '', 1).replace('!', '', 1).replace('>', '', 1))
        if userid == ctx.author.id:
            return await ctx.send('You can\'t restrict yourself :thinking:')
        if userid == ctx.guild.id:
            return await ctx.send('You can\'t restrict your own server :thinking:')
    except:
        return await ctx.send('Invalid user/server!')
    if userid in db['moderators']:
        return await ctx.send(
            'UniChat moderators are immune to blocks!\n(Though, do feel free to report anyone who abuses this immunity.)')
    banlist = []
    if f'{ctx.guild.id}' in list(db['blocked'].keys()):
        banlist = db['blocked'][f'{ctx.guild.id}']
    else:
        db['blocked'].update({f'{ctx.guild.id}': []})
    if userid in banlist:
        return await ctx.send('User/server already banned!')
    db['blocked'][f'{ctx.guild.id}'].append(userid)
    db.save_data()
    await ctx.send('User/server can no longer forward messages to this channel!')

@bot.command(aliases=['globalban'],hidden=True,description='Blocks a user or server from bridging messages through Unifier.')
async def ban(ctx, target, duration, *, reason='no reason given'):
    if not ctx.author.id in db['moderators']:
        return
    forever = (duration.lower() == 'inf' or duration.lower() == 'infinite' or
               duration.lower() == 'forever' or duration.lower() == 'indefinite')
    if forever:
        duration = 0
    else:
        try:
            duration = timetoint(duration)
        except:
            return await ctx.send('Invalid duration!')
    try:
        userid = int(target.replace('<@', '', 1).replace('!', '', 1).replace('>', '', 1))
        if userid == ctx.author.id:
            return await ctx.send('You can\'t restrict yourself :thinking:')
    except:
        return await ctx.send('Invalid user/server!')

    if userid in db['moderators'] and not ctx.author.id == config['owner']:
        return await ctx.send('Moderators can\'t moderate other moderators!')
    banlist = db['banned']
    if userid in banlist:
        return await ctx.send('User/server already banned!')
    ct = round(time.time())
    nt = ct + duration
    if forever:
        nt = 0
    db['banned'].update({f'{userid}': nt})
    db.save_data()
    if ctx.author.discriminator == '0':
        mod = f'@{ctx.author.name}'
    else:
        mod = f'{ctx.author.name}#{ctx.author.discriminator}'
    embed = nextcord.Embed(title=f'You\'ve been __global restricted__ by {mod}!', description=reason, color=0xffcc00,
                           timestamp=datetime.datetime.now(datetime.timezone.utc))
    try:
        embed.set_author(name=mod, icon_url=ctx.author.avatar)
    except:
        embed.set_author(name=mod)
    if forever:
        embed.colour = 0xff0000
        embed.add_field(name='Actions taken',
                        value=f'- :zipper_mouth: Your ability to text and speak have been **restricted indefinitely**. This will not automatically expire.\n- :white_check_mark: You must contact a moderator to appeal this restriction.',
                        inline=False)
    else:
        embed.add_field(name='Actions taken',
                        value=f'- :warning: You have been **warned**. Further rule violations may lead to sanctions on the Unified Chat global moderators\' discretion.\n- :zipper_mouth: Your ability to text and speak have been **restricted** until <t:{nt}:f>. This will expire <t:{nt}:R>.',
                        inline=False)
    user = bot.get_user(userid)
    if not user:
        return await ctx.send('User was global banned!')
    if user:
        try:
            await user.send(embed=embed)
        except:
            pass

    await ctx.send('User was global banned!')

@bot.command(aliases=['unban'],description='Unblocks a user or server from bridging messages to your server.')
async def unrestrict(ctx, target):
    if not (ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.kick_members or
            ctx.author.guild_permissions.ban_members):
        return await ctx.send('You cannot unrestrict members/servers.')
    try:
        userid = int(target.replace('<@', '', 1).replace('!', '', 1).replace('>', '', 1))
    except:
        return await ctx.send('Invalid user/server!')
    banlist = []
    if f'{ctx.guild.id}' in list(db['blocked'].keys()):
        banlist = db['blocked'][f'{ctx.guild.id}']
    if not userid in banlist:
        return await ctx.send('User/server not banned!')
    db['blocked'][f'{ctx.guild.id}'].remove(userid)
    db.save_data()
    await ctx.send('User/server can now forward messages to this channel!')

@bot.command(hidden=True,description='Unblocks a user or server from bridging messages through Unifier.')
async def globalunban(ctx, *, target):
    if not ctx.author.id in db['moderators']:
        return
    try:
        userid = int(target.replace('<@', '', 1).replace('!', '', 1).replace('>', '', 1))
    except:
        return await ctx.send('Invalid user/server!')
    banlist = db['banned']
    if not f'{userid}' in list(banlist.keys()):
        return await ctx.send('User/server not banned!')
    db['banned'].pop(f'{userid}')
    db.save_data()
    await ctx.send('unbanned, nice')

@bot.command(aliases=['find'],description='Identifies the origin of a message.')
async def identify(ctx):
    if not (ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.kick_members or
            ctx.author.guild_permissions.ban_members) and not ctx.author.id in db['moderators']:
        return
    try:
        msg = ctx.message.reference.cached_message
        if msg == None:
            msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
    except:
        return await ctx.send('Invalid message!')
    try:
        msg_obj: UnifierMessage = await fetch_message(msg.id)
    except:
        return await ctx.send('Could not find message in cache!')

    try:
        user = await bot.fetch_user(int(msg_obj.author_id))
        username = user.name
    except:
        username = '[unknown]'

    try:
        guild = bot.get_guild(int(msg_obj.guild_id))
        guildname = guild.name
    except:
        guildname = '[unknown]'

    await ctx.send(f'Sent by @{username} ({msg_obj.author_id}) in {guildname} ({msg_obj.guild_id})')

@bot.command(description='Deletes a message.')
async def delete(ctx, *, msg_id=None):
    """Deletes all bridged messages. Does not delete the original."""
    gbans = db['banned']
    ct = time.time()
    if f'{ctx.author.id}' in list(gbans.keys()):
        banuntil = gbans[f'{ctx.author.id}']
        if ct >= banuntil and not banuntil == 0:
            db['banned'].pop(f'{ctx.author.id}')
            db.save_data()
        else:
            return
    if f'{ctx.guild.id}' in list(gbans.keys()):
        banuntil = gbans[f'{ctx.guild.id}']
        if ct >= banuntil and not banuntil == 0:
            db['banned'].pop(f'{ctx.guild.id}')
            db.save_data()
        else:
            return
    if f'{ctx.author.id}' in list(gbans.keys()) or f'{ctx.guild.id}' in list(gbans.keys()):
        return await ctx.send('Your account or your guild is currently **global restricted**.')

    try:
        msg_id = ctx.message.reference.message_id
    except:
        if not msg_id:
            return await ctx.send('No message!')

    try:
        msg: UnifierMessage = await fetch_message(msg_id)
    except:
        return await ctx.send('Could not find message in cache!')

    if not ctx.author.id==msg.author_id and not ctx.author.id in db['moderators']:
        return await ctx.send('You didn\'t send this message!')

    try:
        guild = bot.get_guild(int(msg.guild_id))
        ch = guild.get_channel(int(msg.channel_id))
        todelete = await ch.fetch_message(int(msg.id))
        await todelete.delete()
        return await ctx.send('Deleted message (parent deleted, copies will follow)')
    except:
        deleted = 0

        try:
            for guild_id in list(msg.copies.keys()):
                guild = bot.get_guild(int(guild_id))
                if not guild:
                    continue
                try:
                    webhook = await bot.fetch_webhook(db['rooms'][msg.room][f'{guild.id}'][0])
                    await webhook.delete_message(msg.copies[guild_id])
                    deleted += 1
                except:
                    continue

            return await ctx.send(f'Deleted message ({deleted} copies deleted)')
        except:
            logger.exception('Something went wrong!')
            await ctx.send('Something went wrong.')

@bot.command(description='Shows bot info.')
async def about(ctx):
    embed = nextcord.Embed(title=bot.user.name, description="Powered by Unifier Micro")
    embed.add_field(name="Developers",value="@green.\n@itsasheer",inline=False)
    embed.add_field(name="View source code", value=config['repo'], inline=False)
    embed.set_footer(text=f"Version {version}")
    await ctx.send(embed=embed)

@bot.event
async def on_message(message):
    if not message.webhook_id == None:
        # webhook msg
        return

    if message.author.id == bot.user.id:
        return

    if message.content.startswith(bot.command_prefix) and not message.author.bot:
        return await bot.process_commands(message)

    try:
        hooks = await message.channel.webhooks()
    except:
        return

    roomname = None
    for room in list(db['rooms'].keys()):
        try:
            for hook in hooks:
                if hook.id == db['rooms'][room][f'{message.guild.id}'][0]:
                    roomname = room
                    break
        except:
            continue
        if roomname:
            break

    if not roomname:
        return

    if ('nextcord.gg/' in message.content or 'nextcord.com/invite/' in message.content or
            'discordapp.com/invite/' in message.content):
        try:
            await message.delete()
        except:
            pass
        return await message.channel.send(f'<@{message.author.id}> Invites aren\'t allowed!')

    gbans = db['banned']
    ct = time.time()
    if f'{message.author.id}' in list(gbans.keys()):
        banuntil = gbans[f'{message.author.id}']
        if ct >= banuntil and not banuntil == 0:
            db['banned'].pop(f'{message.author.id}')
            db.save_data()
        else:
            return
    if f'{message.guild.id}' in list(gbans.keys()):
        banuntil = gbans[f'{message.guild.id}']
        if ct >= banuntil and not banuntil == 0:
            db['banned'].pop(f'{message.guild.id}')
            db.save_data()
        else:
            return

    if is_room_locked(roomname,db) and not message.author.id in db['moderators']:
        return

    limit_notified = False
    reply_msg = None
    trimmed = None
    donotshow = False
    bridged = {}

    if message.reference:
        try:
            reply_msg = await fetch_message(message.reference.message_id)
        except:
            pass
        try:
            msg = message.reference.cached_message
            if not msg:
                msg = await message.channel.fetch_message(message.reference.message_id)

            trimmed = msg.content
            if len(msg.content) > 80:
                trimmed = trimmed[:-(len(msg.content)-77)].replace('\n',' ')
                while trimmed.endswith(' '):
                    trimmed = trimmed[:-1]
                trimmed = trimmed + '...'
            if len(trimmed)==0:
                trimmed = None
        except:
            pass

    if not trimmed:
        donotshow = True

    for guild_id in list(db['rooms'][roomname].keys()):
        if int(guild_id)==message.guild.id:
            continue
        guild = bot.get_guild(int(guild_id))
        if not guild:
            continue

        size_total = 0
        files = []
        for attachment in message.attachments:
            size_total += attachment.size
            if size_total > 25000000:
                if not limit_notified:
                    limit_notified = True
                    await message.channel.send('Your files passed the 25MB limit. Some files will not be sent.',
                                               reference=message)
                break
            try:
                files.append(await attachment.to_file(use_cached=True, spoiler=attachment.is_spoiler()))
            except:
                files.append(await attachment.to_file(use_cached=True, spoiler=False))

        webhook: nextcord.Webhook = await bot.fetch_webhook(db['rooms'][roomname][f'{guild.id}'][0])
        components = None

        if reply_msg:
            components = ui.MessageComponents()
            components.add_rows(
                ui.ActionRow(
                    nextcord.ui.Button(
                        style=nextcord.ButtonStyle.gray,
                        label=f'Replying to [unknown]',
                        disabled=True
                    )
                ),
                ui.ActionRow(
                    nextcord.ui.Button(
                        style=nextcord.ButtonStyle.blurple,
                        label=f'x{len(message.attachments)}',
                        emoji='\U0001F3DE',
                        disabled=True
                    ) if donotshow else nextcord.ui.Button(
                        style=nextcord.ButtonStyle.blurple,
                        label=trimmed,
                        disabled=True
                    )
                )
            )

            ch = guild.get_channel(webhook.channel_id)
            if ch:
                url = f'https://nextcord.com/channels/{guild.id}/{ch.id}/{reply_msg.id}'
                try:
                    reply_author = await bot.fetch_user(int(reply_msg.author_id))
                    reply_name = '@'+reply_author.global_name or reply_author.name
                except:
                    reply_name = '[unknown]'

                components = ui.MessageComponents()
                components.add_rows(
                    ui.ActionRow(
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.url,
                            label=f'Replying to {reply_name}',
                            url=url
                        )
                    ),
                    ui.ActionRow(
                        nextcord.ui.Button(
                            style=nextcord.ButtonStyle.blurple,
                            label=f'x{len(message.attachments)}',
                            emoji='\U0001F3DE',
                            disabled=True
                        ) if donotshow else nextcord.ui.Button(
                            style=nextcord.ButtonStyle.blurple,
                            label=trimmed,
                            disabled=True
                        )
                    )
                )

        try:
            url = message.author.avatar.url
        except:
            url = None

        sent = await webhook.send(
            avatar_url=url,
            username=message.author.global_name or message.author.name,
            files=files,
            view=components if components else ui.MessageComponents(),
            content=message.content,
            wait=True
        )
        bridged.update({f'{guild.id}':sent.id})

    messages.append(
        UnifierMessage(
            author_id=message.author.id,
            guild_id=message.guild.id,
            channel_id=message.channel.id,
            original=message.id,
            copies=bridged,
            room=roomname
        )
    )

@bot.event
async def on_message_edit(before, after):
    if before.content == after.content:
        return
    message = after

    if not message.webhook_id == None:
        # webhook msg
        return

    try:
        msg: UnifierMessage = await fetch_message(message.id)
    except:
        return

    roomname = msg.room

    if not roomname:
        return

    if is_room_locked(roomname,db) and not message.author.id in db['moderators']:
        return

    for guild_id in list(db['rooms'][roomname].keys()):
        if int(guild_id)==message.guild.id:
            continue
        guild = bot.get_guild(int(guild_id))

        try:
            msg_id = int(await msg.fetch_id(str(guild.id)))
            webhook = await bot.fetch_webhook(db['rooms'][roomname][f'{guild.id}'][0])
        except:
            continue

        await webhook.edit_message(
            message_id=msg_id,
            content=message.content
        )

@bot.event
async def on_message_delete(message):
    if not message.webhook_id == None:
        # webhook msg
        return

    try:
        msg: UnifierMessage = await fetch_message(message.id)
    except:
        return

    roomname = msg.room

    for guild_id in list(db['rooms'][roomname].keys()):
        if int(guild_id)==message.guild.id:
            continue
        guild = bot.get_guild(int(guild_id))

        try:
            msg_id = int(await msg.fetch_id(str(guild.id)))
            webhook = await bot.fetch_webhook(db['rooms'][roomname][f'{guild.id}'][0])
        except:
            continue

        await webhook.delete_message(msg_id)

bot.run(os.environ.get('TOKEN'))
