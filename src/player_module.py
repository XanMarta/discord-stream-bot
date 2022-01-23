from discord import guild
from bot_module import BotModule
import discord, time
import subprocess, os, shlex
import signal, sys
from dotenv import load_dotenv
import asyncio


class PlayerModule(BotModule):
    # Control stream process and voice
    # Run before VLC module
    def __init__(self):
        load_dotenv()
        self.video_device = os.environ['VIDEO_DEVICE']
        self.voice_channel = None
        self.voice_client = None
        self.stream_proc = None
        self.pipe_proc = None
        self.stream_proc_id = 1000
        self.__is_joining = False
        self.__is_playing = False
        # Global
        self.guild_id = ""
        self.voice_id = ""
    
    def __play_next(self):
        print("Starting pipe audio ...")
        guild = self.bot.get_guild(self.guild_id)
        self.voice_client = discord.utils.get(self.bot.voice_clients, guild=guild)
        self.pipe_proc = subprocess.Popen(["cat", "/tmp/audio"], stdout=subprocess.PIPE)
        self.voice_client.play(discord.FFmpegPCMAudio(self.pipe_proc.stdout, pipe=True), after=lambda e: self.__play_next)
    
    def __start_stream(self, sub=None):
        if self.stream_proc is None:
            # Kill current running ffmpeg first
            subprocess.Popen(['pkill', 'ffmpeg']).communicate()
            print(f"Starting stream ...")
            print(f"Subtitle: {sub}")
            if sub is not None and os.path.isfile(sub):
                sf = f",subtitles={sub}"
            else:
                sf = ""
            command = f"ffmpeg -re -i 'udp://127.0.0.1:8082?overrun_nonfatal=1&fifo_size=278876' -ac 2 -ar 48000 -vf 'scale=w=1280:h=720:force_original_aspect_ratio=1,pad=1280:720:(ow-iw)/2:(oh-ih)/2,fps=30{sf}' -pix_fmt rgb24 -f v4l2 {self.video_device} -f avi pipe:1 > /tmp/audio"
            self.stream_proc = subprocess.Popen(command, stderr=subprocess.STDOUT, shell=True, preexec_fn=os.setsid)
            self.stream_proc_id = self.stream_proc.pid

    def __exit_signal(self, signum, frame):
        if self.stream_proc is not None:
            os.killpg(os.getpgid(self.stream_proc_id), signal.SIGTERM)
            self.stream_proc = None
        print("Bye!")
        sys.exit(1)
    
    def __set_command(self):
        async def p_test(ctx, arg):
            guild = self.bot.get_guild(self.guild_id)
            self.voice_channel = discord.utils.get(guild.voice_channels, id=self.voice_id)
            await self.voice_channel.connect()
        self.add_func("p_test", p_test)

        async def p_next(ctx, arg):
            self.__play_next()
        self.add_func("p_next", p_next)

    # Bot command
    
    async def p_prepare(self):
        if not os.path.exists("/tmp/audio"):
            os.mkfifo("/tmp/audio")
        signal.signal(signal.SIGINT, self.__exit_signal)
        # self.__set_command()  # Test only
    
    async def p_join(self, sub=None):
        if not self.__is_joining:
            guild = self.bot.get_guild(self.guild_id)
            self.voice_channel = discord.utils.get(guild.voice_channels, id=self.voice_id)
            await self.voice_channel.connect()
            self.__start_stream(sub)
            await asyncio.sleep(1)
            self.__play_next()
            self.__is_joining = True

    async def p_leave(self):
        if self.__is_joining:
            if self.__is_playing:
                await self.p_stop()
            guild = self.bot.get_guild(self.guild_id)
            self.voice_client = discord.utils.get(self.bot.voice_clients, guild=guild)
            if self.voice_client.is_playing():
                self.voice_client.stop()
            await self.voice_client.disconnect()
            if self.stream_proc is not None:
                print("Terminating stream ...")
                os.killpg(os.getpgid(self.stream_proc_id), signal.SIGTERM)
                self.stream_proc = None
            if self.pipe_proc is not None:
                self.pipe_proc.terminate()
                self.pipe_proc = None
            self.__is_joining = False

    async def p_play(self, sub_file=None):
        if not self.__is_playing:
            if not self.__is_joining:
                await self.p_join(sub_file)
            self.__is_playing = True

    async def p_stop(self):
        self.__is_playing = False


if __name__ == '__main__':
    program = PlayerModule()
    program.set_player_command()
    program.start_bot()
