from pythonopensubtitles.opensubtitles import OpenSubtitles
from bot_module import BotModule
from youtube_dl import YoutubeDL
from dotenv import load_dotenv
from validators.url import url as url_val
from urllib.parse import urlparse
import os, traceback


class MediaModule(BotModule):
    def __init__(self):
        load_dotenv()
        self.media_path = os.path.abspath(os.environ['MEDIA_PATH'])
        self.media_list = []
        self.sub_list = []
        self.sub_dir = os.path.abspath(os.environ['DIST_PATH'])
        self.sub_path = os.path.join(self.sub_dir, "subtitle.srt")
        # Selected variables
        self.sub_choose = None
        self.media_choose = None
        self.sub_name = "None"
        self.media_name = "None"
        # Private
        self.ost = OpenSubtitles()
        self.ost_username = os.environ['OPENSUBTITLES_USERNAME']
        self.ost_password = os.environ['OPENSUBTITLES_PASSWORD']
        self.ost_token = None
        self.ost_languages = ["vie", "eng"]
    
    def start(self):
        # Login ost
        print("Logging to ost ...")
        self.ost_token = self.ost.login(self.ost_username, self.ost_password)
        # Bot command
        async def search_media(ctx, arg):
            self.media_list = [f for f in os.listdir(self.media_path) if os.path.isfile(os.path.join(self.media_path, f))]
            result = "**Media list:**\n\n"
            for i, media in enumerate(self.media_list):
                result += f"{i}  -  {media}\n"
            await self.send_back(ctx, result)
        self.add_func("search", search_media)
        self.add_func("searchmedia", search_media)

        async def select_media(ctx, arg):
            if len(arg) != 1:
                await self.send_back(ctx, "Invalid params")
            else:
                try:
                    index = int(arg[0])
                    self.media_choose = self.sel_media(index)
                    if self.media_choose is None:
                        await self.send_back(ctx, "Invalid params")
                    else:
                        await self.send_back(ctx, f"Media selected: {self.media_name}")
                except:
                    await self.send_back(ctx, "Invalid params")
        self.add_func("select", select_media)
        self.add_func("selectmedia", select_media)

        async def search_sub(ctx, arg):
            if self.ost_token is None:
                await self.send_back(ctx, "Subtitle feature is not ready")
            else:
                try:
                    await self.react_loading(ctx)
                    search_list = [{"query": arg, "sublanguageid": lan} for lan in self.ost_languages]
                    self.sub_list = [res for query in search_list for res in self.ost.search_subtitles([query])]
                    result = "**--- List subtitles ---**\n\n"
                    for i, sub in enumerate(self.sub_list):
                        result += f"{i}  -  {sub['SubFileName'][:50]}  -  {sub['SubLanguageID'].upper()}\n"
                    await self.send_back(ctx, result)
                    await self.react_yes(ctx)
                except:
                    traceback.print_exc()
                    await self.send_back(ctx, "Cannot search subtitle")
                    await self.react_yes(ctx)
        self.add_func("searchsub", search_sub, arg_parse=False)

        async def select_sub(ctx, arg):
            if self.ost_token is None:
                await self.send_back(ctx, "Subtitle feature is not ready")
            else:
                await self.react_loading(ctx)
                try:
                    index = int(arg[0])
                    sub = self.sel_sub(index)
                    if sub is None:
                        await self.send_back(ctx, "Invalid params")
                    else:
                        self.sub_choose = self.sub_path
                        await self.react_yes(ctx)
                        await self.send_back(ctx, f"Subtitle selected: {self.sub_name[:50]}")
                except:
                    traceback.print_exc()
                    await self.send_back(ctx, "Invalid params")
                await self.react_yes(ctx)
        self.add_func("selectsub", select_sub)

        # Special source

        async def add_youtube(ctx, arg):
            if len(arg) != 1:
                await self.send_back(ctx, "Invalid params")
            else:
                await self.react_loading(ctx)
                url, title = self.get_youtube(arg[0])
                if url is None:
                    await self.send_back(ctx, "Cannot get youtube url")
                else:
                    self.media_choose = url
                    self.media_name = f"[Youtube] {title}"
                    await self.send_back(ctx, f"Media selected: {title}")
                await self.react_yes(ctx)
        self.add_func("addyt", add_youtube)

        async def add_url(ctx, arg):
            if len(arg) != 1:
                await self.send_back(ctx, "Invalid params")
            else:
                url = arg[0]
                if not url_val(url):
                    await self.send_back(ctx, "Invalid source")
                else:
                    self.media_choose = url
                    self.media_name = url
                    await self.send_back(ctx, f"Media selected: {url}")
                    await self.react_yes(ctx)
        self.add_func("addurl", add_url)
    
    # Private method

    def sel_media(self, index):
        if 0 <= index < len(self.media_list):
            self.media_name = self.media_list[index]
            return os.path.abspath(os.path.join(self.media_path, self.media_list[index]))
        else:
            self.media_name = "None"
            return None

    def sel_sub(self, index):
        if 0 <= index < len(self.sub_list):
            sub = self.sub_list[index]
            self.ost.download_subtitles([sub['IDSubtitleFile']], 
                    override_filenames={sub['IDSubtitleFile']: "subtitle.srt"},
                    output_directory=self.sub_dir,
                    extension="srt")
            self.sub_name = sub['SubFileName']
            return self.sub_path
        else:
            self.sub_name = "None"
            return None

    # Public methods
    
    def get_youtube(self, url):
        ydl = YoutubeDL({
            'format': 'best'
        })
        try:
            r = ydl.extract_info(url, download=False)
            info = [f['url'] for f in r['formats'] if f['acodec'] != 'none' and f['vcodec'] != 'none']
            if len(info) > 0:
                return info[0], r['title']
            else:
                return None, "None"
        except:
            return None, "None"
    
    def select_media(self, path):  # none, index, url
        if path is None:
            return self.media_choose
        else:
            try:
                index = int(path)
                media = self.sel_media(index)
                return media
            except:
                if not url_val(path):
                    return None
                else:
                    parsed = urlparse(path)
                    if parsed.netloc in ['www.youtube.com', 'youtube.com', 'www.youtu.be', 'youtu.be']:
                        url, title = self.get_youtube(path)
                        self.media_name = title
                        return url
                    else:
                        self.media_name = path
                        return path
    
    def select_sub(self, path):  # none, index, url
        if path is None:
            return self.sub_choose
        else:
            try:
                index = int(path)
                return self.sel_sub(index)
            except:
                self.sub_name = "None"
                return None  # Note: handle url here
    
    def get_info(self):
        return self.media_name, self.sub_name
    
    def reset_media_info(self):
        self.sub_choose = None
        self.media_choose = None
        self.sub_name = "None"
        self.media_name = "None"



if __name__ == "__main__":
    program = MediaModule()
    print(program.media_path)
