"""
Unifier Micro - A much lighter version of Unifier
Copyright (C) 2024  Green

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import discord
from discord.ext import commands
import json
import logging
import time
import datetime

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

class CustomFormatter(logging.Formatter):
    def __init__(self, count):
        super().__init__()
        log_colors = {
            'debug': '\x1b[45;1m',
            'info': '\x1b[36;1m',
            'warning': '\x1b[33;1m',
            'error': '\x1b[31;1m',
            'critical': '\x1b[37;41m',
        }

        self.log_formats = {
            logging.DEBUG: logging.Formatter(
                f'\x1b[30;1m%(asctime)s\x1b[0m | \U0001F6E0  {log_colors["debug"]}%(levelname)-8s\x1b[0m \x1b[35m%(name)-{count}s\x1b[0m %(message)s',
                '%Y-%m-%d %H:%M:%S',
            ),
            logging.INFO: logging.Formatter(
                f'\x1b[30;1m%(asctime)s\x1b[0m | \U0001F4DC {log_colors["info"]}%(levelname)-8s\x1b[0m \x1b[35m%(name)-{count}s\x1b[0m %(message)s',
                '%Y-%m-%d %H:%M:%S',
            ),
            logging.WARNING: logging.Formatter(
                f'\x1b[30;1m%(asctime)s\x1b[0m | \U00002755 {log_colors["warning"]}%(levelname)-8s\x1b[0m \x1b[35m%(name)-{count}s\x1b[0m %(message)s',
                '%Y-%m-%d %H:%M:%S',
            ),
            logging.ERROR: logging.Formatter(
                f'\x1b[30;1m%(asctime)s\x1b[0m | \U0000274C {log_colors["error"]}%(levelname)-8s\x1b[0m \x1b[35m%(name)-{count}s\x1b[0m %(message)s',
                '%Y-%m-%d %H:%M:%S',
            ),
            logging.CRITICAL: logging.Formatter(
                f'\x1b[30;1m%(asctime)s\x1b[0m | \U0001F6D1 {log_colors["critical"]}%(levelname)-8s\x1b[0m \x1b[35m%(name)-{count}s\x1b[0m %(message)s',
                '%Y-%m-%d %H:%M:%S',
            ),
            'unknown': logging.Formatter(
                f'\x1b[30;1m%(asctime)s\x1b[0m | \U00002754 %(levelname)-8s\x1b[0m \x1b[35m%(name)-{count}s\x1b[0m %(message)s',
                '%Y-%m-%d %H:%M:%S',
            )
        }

    def format(self, log):
        useformat = self.log_formats.get(log.levelno)
        if not useformat:
            useformat = self.log_formats.get('unknown')

        if log.exc_info:
            text = useformat.formatException(log.exc_info)
            log.exc_text = f'\x1b[31m{text}\x1b[0m'
            output = useformat.format(log)
            log.exc_text = None
        else:
            output = useformat.format(log)

        return output

def buildlogger(package, name, level, handler=None):
    if not handler:
        handler = logging.StreamHandler()

    handler.setLevel(level)
    handler.setFormatter(CustomFormatter(len(package) + 5))
    library, _, _ = __name__.partition('.')
    logger = logging.getLogger(package + '.' + name)

    # Prevent duplicate output
    while logger.hasHandlers():
        logger.removeHandler(logger.handlers[0])

    logger.setLevel(level)
    logger.addHandler(handler)
    return logger

def is_user_admin(id):
    try:
        global admin_ids
        if id in admin_ids:
            return True
        else:
            return False
    except:
        return False

def is_room_restricted(room,db):
    try:
        if room in db['restricted']:
            return True
        else:
            return False
    except:
        return False

def is_room_locked(room,db):
    try:
        if room in db['locked']:
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


with open('config.json', 'r') as file:
    config = json.load(file)

level = logging.DEBUG if config['debug'] else logging.INFO
package = config['package']
admin_ids = config['admin_ids']

logger = buildlogger(package,'core',level)

db = AutoSaveDict({})
db.load_data()

messages = []

ut_total = round(time.time())
ut_connected = 0
ut_conntime = round(time.time())
ut_measuring = True

intents = discord.Intents(
    emojis=True,
    emojis_and_stickers=True,
    guild_messages=True,
    guilds=True,
    message_content=True,
    messages=True,
    webhooks=True
)
mentions = discord.AllowedMentions(everyone=False, roles=False, users=False)

bot = commands.Bot(command_prefix=config['prefix'], intents=intents)

asciiart = """  _    _       _  __ _           
 | |  | |     (_)/ _(_)          
 | |  | |_ __  _| |_ _  ___ _ __ 
 | |  | | '_ \\| |  _| |/ _ \\ '__|
 | |__| | | | | | | | |  __/ |   
  \\____/|_| |_|_|_| |_|\\___|_| """

print(asciiart)
print('Micro edition')
print('Version: 1.1.5')
print()

@bot.event
async def on_ready():
    logger.info('Unifier is ready!')

@bot.event
async def on_connect():
    global ut_measuring
    global ut_conntime
    if not ut_measuring:
        ut_measuring = True
        ut_conntime = round(time.time())

@bot.event
async def on_disconnect():
    global ut_measuring
    global ut_connected
    global ut_conntime
    if ut_measuring:
        ut_connected += round(time.time()) - ut_conntime
        ut_measuring = False

@bot.command()
async def uptime(ctx):
    embed = discord.Embed(
        title=f'{bot.user.global_name} uptime',
        description=f'The bot has been up since <t:{ut_total}:f>.'
    )
    t = ut_connected + round(time.time()) - ut_conntime
    td = datetime.timedelta(seconds=t)
    d = td.days
    h, m, s = str(td).split(':')
    tup = t
    embed.add_field(
        name='Total uptime',
        value=f'`{d}` days, `{int(h)}` hours, `{int(m)}` minutes, `{int(s)}` seconds',
        inline=False
    )
    t = ut_connected + round(time.time()) - ut_conntime
    td = datetime.timedelta(seconds=t)
    d = td.days
    h, m, s = str(td).split(':')
    embed.add_field(
        name='Connected uptime',
        value=f'`{d}` days, `{int(h)}` hours, `{int(m)}` minutes, `{int(s)}` seconds',
        inline=False
    )
    embed.add_field(
        name='Connected uptime %',
        value=f'{round((t/tup)*100,2)}%',
        inline=False
    )
    await ctx.send(embed=embed)

@bot.command(hidden=True)
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
    if is_user_admin(userid):
        return await ctx.send('are you fr')
    db['moderators'].append(userid)
    db.save_data()
    mod = f'{user.name}#{user.discriminator}'
    if user.discriminator=='0':
        mod = f'@{user.name}'
    await ctx.send(f'**{mod}** is now a moderator!')

@bot.command(hidden=True,aliases=['remmod','delmod'])
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

@bot.command(aliases=['link', 'connect', 'federate', 'bridge'])
async def bind(ctx, *, room=''):
    if not ctx.author.guild_permissions.manage_channels and not is_user_admin(ctx.author.id):
        return await ctx.send('You don\'t have the necessary permissions.')
    if is_room_restricted(room, db) and not is_user_admin(ctx.author.id):
        return await ctx.send('Only admins can bind channels to restricted rooms.')
    if room == '' or not room:  # Added "not room" as a failback
        room = 'main'
        await ctx.send('**No room was given, defaulting to main**')
    try:
        data = db['rooms'][room]
    except:
        return await ctx.send('This isn\'t a valid room. Try `main`, `pr`, `prcomments`, or `liveries` instead.')
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
        if len(db['rules'][room]) == 0:
            text = f'No rules exist yet for this room! For now, follow the main room\'s rules.\nYou can always view rules if any get added using `{bot.command_prefix}rules {room}`.'
        else:
            for rule in db['rules'][room]:
                if text == '':
                    text = f'1. {rule}'
                else:
                    text = f'{text}\n{index}. {rule}'
                index += 1
        text = f'{text}\n\nPlease display these rules somewhere accessible.'
        embed = discord.Embed(title='Please agree to the room rules first:', description=text)
        embed.set_footer(text='Failure to follow room rules may result in user or server restrictions.')
        ButtonStyle = discord.ButtonStyle
        row = [
            discord.ui.Button(style=ButtonStyle.green, label='Accept and bind', custom_id=f'accept', disabled=False),
            discord.ui.Button(style=ButtonStyle.red, label='No thanks', custom_id=f'reject', disabled=False)
        ]
        btns = discord.ui.ActionRow(row[0], row[1])
        components = discord.ui.MessageComponents(btns)
        msg = await ctx.send(embed=embed, components=components)

        def check(interaction):
            return interaction.user.id == ctx.author.id and (
                    interaction.custom_id == 'accept' or
                    interaction.custom_id == 'reject'
            ) and interaction.channel.id == ctx.channel.id

        try:
            resp = await bot.wait_for("component_interaction", check=check, timeout=60.0)
        except:
            row[0].disabled = True
            row[1].disabled = True
            btns = discord.ui.ActionRow(row[0], row[1])
            components = discord.ui.MessageComponents(btns)
            await msg.edit(components=components)
            return await ctx.send('Timed out.')
        row[0].disabled = True
        row[1].disabled = True
        btns = discord.ui.ActionRow(row[0], row[1])
        components = discord.ui.MessageComponents(btns)
        await resp.response.edit_message(components=components)
        if resp.custom_id == 'reject':
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

@bot.command(aliases=['unlink', 'disconnect'])
async def unbind(ctx, *, room=''):
    if room == '':
        return await ctx.send('You must specify the room to unbind from.')
    if not ctx.author.guild_permissions.manage_channels and not is_user_admin(ctx.author.id):
        return await ctx.send('You don\'t have the necessary permissions.')
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

@bot.command(aliases=['ban'])
async def restrict(ctx, *, target):
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
        userid = target
        if not len(userid) == 26:
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

@bot.command(aliases=['unban'])
async def unrestrict(ctx, *, target):
    if not (ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.kick_members or
            ctx.author.guild_permissions.ban_members):
        return await ctx.send('You cannot unrestrict members/servers.')
    try:
        userid = int(target.replace('<@', '', 1).replace('!', '', 1).replace('>', '', 1))
    except:
        userid = target
        if not len(target) == 26:
            return await ctx.send('Invalid user/server!')
    banlist = []
    if f'{ctx.guild.id}' in list(db['blocked'].keys()):
        banlist = db['blocked'][f'{ctx.guild.id}']
    if not userid in banlist:
        return await ctx.send('User/server not banned!')
    db['blocked'][f'{ctx.guild.id}'].remove(userid)
    db.save_data()
    await ctx.send('User/server can now forward messages to this channel!')


@bot.command(aliases=['find'])
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

@bot.command()
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

@bot.event
async def on_message(message):
    if not message.webhook_id == None:
        # webhook msg
        return

    if message.author.id == bot.user.id:
        return

    if message.content.startswith(bot.command_prefix):
        return await bot.process_commands(message)

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

    hooks = await message.channel.webhooks()

    roomname = None
    for room in list(db['rooms'].keys()):
        try:
            for hook in hooks:
                if hook.id==db['rooms'][room][f'{message.guild.id}'][0]:
                    roomname = room
                    break
        except:
            continue
        if roomname:
            break

    if not roomname:
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

        webhook = await bot.fetch_webhook(db['rooms'][roomname][f'{guild.id}'][0])
        components = None

        if reply_msg:
            components = discord.ui.MessageComponents(
                discord.ui.ActionRow(
                    discord.ui.Button(
                        style=discord.ButtonStyle.gray,
                        label=f'Replying to [unknown]',
                        disabled=True
                    )
                ),
                discord.ui.ActionRow(
                    discord.ui.Button(
                        style=discord.ButtonStyle.blurple,
                        label=f'x{len(message.attachments)}',
                        emoji='\U0001F3DE',
                        disabled=True
                    ) if donotshow else discord.ui.Button(
                        style=discord.ButtonStyle.blurple,
                        label=trimmed,
                        disabled=True
                    )
                )
            )

            ch = guild.get_channel(webhook.channel_id)
            if ch:
                url = f'https://discord.com/channels/{guild.id}/{ch.id}/{reply_msg.id}'
                try:
                    reply_author = await bot.fetch_user(int(reply_msg.author_id))
                    reply_name = '@'+reply_author.global_name
                except:
                    reply_name = '[unknown]'

                components = discord.ui.MessageComponents(
                    discord.ui.ActionRow(
                        discord.ui.Button(
                            style=discord.ButtonStyle.url,
                            label=f'Replying to {reply_name}',
                            url=url
                        )
                    ),
                    discord.ui.ActionRow(
                        discord.ui.Button(
                            style=discord.ButtonStyle.blurple,
                            label=f'x{len(message.attachments)}',
                            emoji='\U0001F3DE',
                            disabled=True
                        ) if donotshow else discord.ui.Button(
                            style=discord.ButtonStyle.blurple,
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
            username=message.author.global_name,
            files=files,
            components=components,
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

bot.run(config['token'])
