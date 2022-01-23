import lib.vlc as vlc
from bot_module import BotModule
import time
import datetime
import os


class VlcModule(BotModule):
    def __init__(self) -> None:
        # Updating
        self.instance = None
        self.player = None
        self.volume = 99
        self.media = None
        self.stream = None
        # Var
        self.playing_state = set([1, 2, 3, 4])
        self.streaming_proc = None
        self.callback = None
        # Global
        self.sub_choose = None  # Media module
    
    def init_player(self):
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()
    
    def vlc_play(self, media, test=False, transcode=False):
        if not self.v_is_playing():
            self.media = self.instance.media_new(media)
            if not test:
                if transcode:
                    self.media.add_option("sout=#transcode{vcodec=mp2v,fps=30,channels=2,soverlay}:std{access=udp,mux=ts,dst=127.0.0.1:8082}")
                    self.media.add_option("no-sout-all")
                else:
                    self.media.add_option("sout=#std{access=udp,mux=ts,dst=127.0.0.1:8082}")
                    self.media.add_option("no-sout-all")
            self.player.set_media(self.media)
            self.player.audio_set_volume(self.volume)
            print("VLC Playing:", media)
            self.player.play()
    
    def vlc_pause(self):
        self.player.set_pause(1)
    
    def vlc_resume(self):
        self.player.set_pause(0)
    
    def vlc_stop(self):
        self.player.stop()
    
    def v_is_playing(self):
        state = self.player.get_state()
        return state in self.playing_state

    # Utility functions
    
    def ms_to_time(self, s):
        return str(datetime.timedelta(seconds=int(s/1000)))
    
    def time_to_ms(self, t):
        try:
            s = 0
            ts = t.split(":")
            if len(ts) >= 1:
                s += int(ts[-1])
            if len(ts) >= 2:
                s += int(ts[-2]) * 60
            if len(ts) >= 3:
                s += int(ts[-3]) * 3600
            return s * 1000
        except:
            return None

    
    def clamp(self, n, minn, maxn):
        return max(min(maxn, n), minn)
    
    # Public command

    def get_player_info(self):  # For info command
        if not self.v_is_playing():
            return None
        else:
            return {
                'length': self.ms_to_time(self.player.get_length()),
                'played': self.ms_to_time(self.player.get_time()),
                'volume': self.player.audio_get_volume()
            }
    
    # Bot command

    async def v_prepare(self):
        self.init_player()
        self.__set_command()

    async def v_join(self):
        pass

    async def v_leave(self):
        self.vlc_stop()

    async def v_play(self, media, transcode=False):
        self.vlc_play(media, transcode=transcode)

    async def v_stop(self):
        self.vlc_stop()
    
    # Media Player command

    async def check_playing(self, ctx):
        if not self.v_is_playing():
            await self.send_back(ctx, "Player is not playing")
            return False
        else:
            return True

    def __set_command(self):
        async def list_audio(ctx, arg):
            if await self.check_playing(ctx):
                message = "**List of audio track:**\n\n"
                audio_list = self.player.audio_get_track_description()
                current_audio = self.player.audio_get_track()
                for i, audio in audio_list:
                    if i == current_audio:
                        message += f"**{i}  -  {audio.decode()}**\n"
                    else:
                        message += f"{i}  -  {audio.decode()}\n"
                await self.send_back(ctx, message)
        self.add_func("listaudio", list_audio)

        async def set_audio(ctx, arg):
            if await self.check_playing(ctx):
                try:
                    index = int(arg[0])
                    r = self.player.audio_set_track(index)
                    if r == 0:
                        await self.react_yes(ctx)
                    else:
                        await self.send_back(ctx, "Invalid audio track")
                except:
                    await self.send_back(ctx, "Invalid audio track")
        self.add_func("setaudio", set_audio)

        async def list_subtitle(ctx, arg):
            if await self.check_playing(ctx):
                message = "**List of subtitle track:**\n\n"
                subtitle_list = self.player.video_get_spu_description()
                current_subtitle = self.player.video_get_spu()
                for i, subtitle in subtitle_list:
                    if i == current_subtitle:
                        message += f"**{i}  -  {subtitle.decode()}**\n"
                    else:
                        message += f"{i}  -  {subtitle.decode()}\n"
                await self.send_back(ctx, message)
        self.add_func("listsub", list_subtitle)

        async def set_subtitle(ctx, arg):
            if await self.check_playing(ctx):
                try:
                    index = int(arg[0])
                    r = self.player.video_set_spu(index)
                    if r == 0:
                        await self.react_yes(ctx)
                    else:
                        await self.send_back(ctx, "Invalid subtitle track")
                except:
                    await self.send_back(ctx, "Invalid subtitle track")
        self.add_func("setsub", set_subtitle)

        async def add_subtitle(ctx, arg):
            if await self.check_playing(ctx):
                if self.sub_choose is None:
                    await self.send_back(ctx, "Subtitle not found")
                else:
                    sub_path = "file://" + self.sub_choose
                    self.player.add_slave(vlc.MediaSlaveType(0), sub_path, True)
                    await self.react_yes(ctx)
        self.add_func("addsub", add_subtitle)

        async def pause(ctx, arg):
            if await self.check_playing(ctx):
                self.vlc_pause()
                await self.react_yes(ctx)
        self.add_func("pause", pause)

        async def resume(ctx, arg):
            if await self.check_playing(ctx):
                self.vlc_resume()
                await self.react_yes(ctx)
        self.add_func("resume", resume)

        async def add_volume(ctx, arg):
            if len(arg) != 1:
                await self.send_back(ctx, "Invalid params")
            else:
                try:
                    v = int(arg[0])
                    if await self.check_playing(ctx):
                        nv = self.player.audio_get_volume() + v
                        nv = self.clamp(nv, 0, 99)
                        self.player.audio_set_volume(nv)
                        await self.react_yes(ctx)
                        await self.send_back(ctx, f"Volume set to {nv}")
                except:
                    await self.send_back(ctx, "Invalid params")
        self.add_func("addvolume", add_volume)

        async def set_volume(ctx, arg):
            if len(arg) != 1:
                await self.send_back(ctx, "Invalid params")
            else:
                try:
                    v = int(arg[0])
                    if await self.check_playing(ctx):
                        nv = self.clamp(v, 0, 99)
                        self.player.audio_set_volume(nv)
                        await self.react_yes(ctx)
                        await self.send_back(ctx, f"Volume set to {nv}")
                except:
                    await self.send_back(ctx, "Invalid params")
        self.add_func("setvolume", set_volume)

        async def forward(ctx, arg):
            if len(arg) != 1:
                await self.send_back(ctx, "Invalid params")
            else:
                try:
                    t = int(arg[0])
                    if await self.check_playing(ctx):
                        nt = self.player.get_time() + t * 1000
                        self.player.set_time(nt)
                        await self.react_yes(ctx)
                        await self.send_back(ctx, f"Time set to {self.ms_to_time(nt)} (+{self.ms_to_time(t*1000)})")
                except:
                    await self.send_back(ctx, "Invalid params")
        self.add_func("forward", forward)
        self.add_func("next", forward)

        async def backward(ctx, arg):
            if len(arg) != 1:
                await self.send_back(ctx, "Invalid params")
            else:
                try:
                    t = int(arg[0])
                    if await self.check_playing(ctx):
                        nt = self.player.get_time() - t * 1000
                        self.player.set_time(nt)
                        await self.react_yes(ctx)
                        await self.send_back(ctx, f"Time set to {self.ms_to_time(nt)} (-{self.ms_to_time(t*1000)})")
                except:
                    await self.send_back(ctx, "Invalid params")
        self.add_func("backward", backward)
        self.add_func("prev", backward)

        async def set_time(ctx, arg):
            if len(arg) != 1:
                await self.send_back(ctx, "Invalid params")
            else:
                if arg[0].find(":") != -1:
                    t = self.time_to_ms(arg[0])
                    if t is None:
                        await self.send_back(ctx, "Invalid time")
                    else:
                        self.player.set_time(t)
                        await self.react_yes(ctx)
                        await self.send_back(ctx, f"Time set to {self.ms_to_time(t)}")
                else:
                    try:
                        t = int(arg[0])
                        if await self.check_playing(ctx):
                            self.player.set_time(t * 1000)
                            await self.react_yes(ctx)
                            await self.send_back(ctx, f"Time set to {self.ms_to_time(t * 1000)}")
                    except:
                        await self.send_back(ctx, "Invalid params")
        self.add_func("settime", set_time)

