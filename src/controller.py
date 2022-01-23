
from vlc_module import VlcModule
from chrome_module import ChromeModule
from player_module import PlayerModule
from bot_module import BotModule
from media_module import MediaModule
import time, os, asyncio


class Controller(VlcModule, ChromeModule, PlayerModule, MediaModule, BotModule):
    def __init__(self) -> None:
        VlcModule.__init__(self)
        ChromeModule.__init__(self)
        PlayerModule.__init__(self)
        MediaModule.__init__(self)
        BotModule.__init__(self)
        self.ct_is_ready = False
        self.ct_is_joining = False
        self.ct_is_playing = False
        # Global
        self.guild_id = ""
        self.channel_id = ""
        self.voice_id = ""
        # Bot check
        self.is_idle = False
        self.idle_start = 0
        self.idle_delay = 3600
    
    async def __is_bot_ready(self, ctx):
        if not self.ct_is_ready:
            await self.react_no(ctx)
            await self.send_back(ctx, "Bot is not ready yet")
            return False
        else:
            self.ct_is_ready = False
            return True
    
    async def __check_invoice(self, ctx):
        if ctx.author.voice is None:
            await self.send_back(ctx, "User is not in voice")
            return False
        else:
            self.guild_id = ctx.guild.id
            self.channel_id = ctx.channel.id
            self.voice_id = ctx.author.voice.channel.id
            return True

    async def __play_media(self, ctx, arg, transcode=False):
        if await self.__is_bot_ready(ctx):
            if await self.__check_invoice(ctx):
                await self.react_loading(ctx)
                if len(arg) > 2:
                    await self.send_back(ctx, "Invalid params")
                else:
                    media_sel = None
                    sub_sel = None
                    if len(arg) == 2:
                        media_sel = arg[0]
                        sub_sel = arg[1]
                    elif len(arg) == 1:
                        media_sel = arg[0]
                    media = self.select_media(media_sel)
                    sub = self.select_sub(sub_sel)
                    # Handle source cases
                    if media is None:
                        await self.send_back(ctx, "Invalid source")
                    else:
                        media_name, sub_name = self.get_info()
                        if transcode:  # For transcode
                            sub = None
                            sub_name = "None"
                        ts = "Yes" if transcode else "No"
                        await self.send_back(ctx, f"**Media played:**\n\n**Media:** {media_name}\n**Subtitle:** {sub_name}\n**Transcode:** {ts}")
                        await self.ct_play(ctx, media, sub, transcode)
                await self.react_yes(ctx)
                self.is_idle = False
            self.ct_is_ready = True 
    
    def __set_command(self):
        # Voice command
        async def join(ctx, arg):
            if await self.__is_bot_ready(ctx):
                if await self.__check_invoice(ctx):
                    await self.react_loading(ctx)
                    await self.ct_join(ctx)
                    await self.react_yes(ctx)
                    self.is_idle = False
                self.ct_is_ready = True
        self.add_func("join", join)

        async def play(ctx, arg):
            await self.__play_media(ctx, arg)
        self.add_func("play", play)

        async def splay(ctx, arg):
            await self.__play_media(ctx, arg, transcode=True)
        self.add_func("splay", splay)

        async def stop(ctx, arg):
            if await self.__is_bot_ready(ctx):
                await self.react_loading(ctx)
                await self.ct_stop(ctx)
                await self.react_yes(ctx)
                self.ct_is_ready = True
                self.is_idle = True
        self.add_func("stop", stop)

        async def leave(ctx, arg):
            if await self.__is_bot_ready(ctx):
                await self.react_loading(ctx)
                await self.ct_leave(ctx)
                await self.react_yes(ctx)
                self.ct_is_ready = True
                self.is_idle = True
                self.idle_start = time.time()
        self.add_func("leave", leave)

        async def end(ctx, arg):
            await ChromeModule.c_end(self)
            await self.react_yes(ctx)
        self.add_func("end", end)

        async def ready():
            await PlayerModule.p_prepare(self)
            await ChromeModule.c_prepare(self)
            await VlcModule.v_prepare(self)
            self.ct_is_ready = True
        self.add_ready(ready)

        async def info(ctx, arg):
            media, sub = self.get_info()
            result = f"**Media:** {media}\n**Subtitle:** {sub}\n"
            player = self.get_player_info()
            if player is None:
                result += "**Status:** Stopped"
            else:
                result += f"**Playing:** {player['played']} / {player['length']}\n"
                result += f"**Volume:** {player['volume']}"
            await self.send_back(ctx, result)
        self.add_func("info", info)

        async def __check_idle():
            if self.is_idle:
                if time.time() - self.idle_start > self.idle_delay:
                    self.stop_driver()
                    self.is_idle = False
        self.start_loop("idle", __check_idle, 300)
    
    # Player controller command
    
    async def ct_join(self, ctx, sub=None):
        if not self.ct_is_joining:
            await PlayerModule.p_join(self, sub)
            await ChromeModule.c_join(self)
            await VlcModule.v_join(self)
            self.ct_is_joining = True
        
    async def ct_play(self, ctx, media, sub=None, transcode=False):
        if not self.ct_is_joining:
            await self.ct_join(ctx, sub)
            await asyncio.sleep(1)
        if not self.ct_is_playing:
            await PlayerModule.p_play(self)
            await ChromeModule.c_play(self)
            await VlcModule.v_play(self, media, transcode)
            self.ct_is_playing = True
        else:
            if self.v_is_playing():
                await self.send_back(ctx, "Already play")
    
    async def ct_stop(self, ctx):
        if self.ct_is_joining:
            if self.ct_is_playing:
                await PlayerModule.p_stop(self)
                await ChromeModule.c_stop(self)
                await VlcModule.v_stop(self)
                self.reset_media_info()
                self.ct_is_playing = False
    
    async def ct_leave(self, ctx):
        if self.ct_is_playing:
            await self.ct_stop(ctx)
            await asyncio.sleep(1)
        if self.ct_is_joining:
            await PlayerModule.p_leave(self)
            await ChromeModule.c_leave(self)
            await VlcModule.v_leave(self)
            self.ct_is_joining = False
    
    def start(self):
        self.__set_command()
        MediaModule.start(self)
        self.start_bot()


if __name__ == "__main__":
    test = Controller()
    test.start()
