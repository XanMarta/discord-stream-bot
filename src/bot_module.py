from discord.ext import commands, tasks
from discord.ext.commands import CommandNotFound
from discord import Embed
from discord.errors import HTTPException
import discord
import asyncio
import os
from dotenv import load_dotenv
from bot_help import generate_help


class BotModule:
    def __init__(self):
        # print('Constructor bot')
        # Super-parameter
        load_dotenv()
        self.bot_token = os.environ['DISCORD_TOKEN']
        self.prefix = '>'
        # Other vars
        self.bot = commands.Bot(command_prefix=self.prefix, help_command=None)
        self.func_loop = {}
        self.func_ready = []
        self._help = generate_help(self.prefix)

    def __set_command(self):
        @self.bot.event
        async def on_ready():
            print(f'{self.bot.user} has connected to Discord')
            for func in self.func_ready:
                await func()

        @self.bot.event
        async def on_command_error(ctx, error):
            if isinstance(error, CommandNotFound):
                await self.send_back(ctx, f'Command not found. Use `{self.bot.command_prefix}help` to see the command list.')
                return
            raise error

        async def __help(ctx, arg):
            await self.send_embed(ctx, self._help)
        self.add_func('help', __help)

        async def __hello(ctx, arg):
            await self.send_back(ctx, "Hello there!")
        self.add_func('hello', __hello)

    # Reply function

    async def react_yes(self, ctx):
        await ctx.message.add_reaction("✅")

    async def react_no(self, ctx):
        await ctx.message.add_reaction("🚫")
    
    async def react_loading(self, ctx):
        await ctx.message.add_reaction("⌛")

    async def send_back(self, ctx, msg, embed=False, text_based=False):
        if len(msg) > 2000:
            msg = msg[:1970]
            msg += '\n*(message cut)*'
        if embed:
            e = Embed()
            e.title = 'Thank you!'
            e.description = msg
            return await ctx.send(embed=e)
        else:
            if text_based:
                msg = "```" + msg + "```"
            return await ctx.send(f'>>> {msg}')

    async def send_embed(self, ctx, embed):
        return await ctx.send(embed=embed)

    async def send_files(self, ctx, files, msg=""):
        file_list = []
        for f in files:
            if os.path.isfile(f):
                file_list.append(f)
        if len(file_list) < len(files):
            print(f'ERROR: {len(files) - len(file_list)} files not found')
        while len(file_list) > 0:
            if len(file_list) > 10:
                file_upload = file_list[:10]
                file_list = file_list[10:]
            else:
                file_upload = file_list
                file_list = []
            file_send = []
            file_discord = []
            for path in file_upload:
                f = open(path, 'rb')
                file_send.append(f)
                file_discord.append(discord.File(f, filename=os.path.basename(path)))
            try:
                await ctx.send(msg, files=file_discord)
            except HTTPException:
                print('ERROR: File is too large to upload')
                await self.send_back(ctx, 'ERROR: File is too large to upload')
            finally:
                for f in file_send:
                    f.close()

    # Public function

    def add_func(self, cmd, func, arg_parse=True):
        setattr(self, cmd, func)
        if arg_parse:
            @self.bot.command(name=cmd)
            async def f(ctx, *args):
                await getattr(self, cmd)(ctx, args)
        else:
            @self.bot.command(name=cmd)
            async def f(ctx, *, args):
                await getattr(self, cmd)(ctx, args)
    
    def add_ready(self, func):
        self.func_ready.append(func)

    def start_loop(self, name, func, delay):
        @tasks.loop(seconds=delay)
        async def f():
            await func()
        self.func_loop[name] = f
        f.start()

    def cancel_loop(self, name):
        if name in self.func_loop:
            self.func_loop[name].cancel()

    def run_async(self, func):
        asyncio.run_coroutine_threadsafe(func, self.bot.loop)

    def start_bot(self):
        self.__set_command()
        print('Starting bot ...')
        self.bot.run(self.bot_token)
