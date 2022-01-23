from audioop import add
from discord import Embed


pre = ""
cmd = ""
desc = ""
cmd_count = 0


def __create_help():
    add_title("Before streaming")
    add_cmd("search", "", "Search for media (from Google Drive)")
    add_cmd("select", "<index>", "Select media from search list")
    add_cmd("searchsub", "<string>", "Search for subtitle (from Open Subtitle)")
    add_cmd("selectsub", "<index>", "Select subtitle from search list")
    add_cmd("addyt", "<url>", "Add Youtube media")
    add_cmd("addurl", "<url>", "Add netword media")
    add_title("Join and play")
    add_cmd("join", "", "Join voice chat")
    add_cmd("play", "[index/url] [sub_index]", "Play the media")
    add_cmd("splay", "[index/url] [index]", "Play the media with transcode")
    add_title("On streaming")
    add_cmd("info", "", "Get information of current stream")
    add_cmd("pause", "", "Pause the stream")
    add_cmd("resume", "", "Resume the stream")
    add_cmd("listaudio", "", "List of audio track of current stream")
    add_cmd("setaudio", "<index>", "Select an audio track for current stream")
    add_cmd("listsub", "", "List of subtitle track of current stream")
    add_cmd("setsub", "<index>", "Select an subtitle track for current stream")
    add_cmd("addsub", "", "Add an subtitle track from search list")
    add_cmd("addvolume", "<number>", "Add player volume")
    add_cmd("setvolume", "<number>", "Set player volume")
    add_cmd("forward", "<second>", "Forward n seconds")
    add_cmd("next", "<second>", "Forward n seconds")
    add_cmd("backward", "<second>", "Backward n seconds")
    add_cmd("prev", "<second>", "Backward n seconds")
    add_cmd("settime", "<time>", "Jump to time")
    add_title("After streaming")
    add_cmd("stop", "", "Stop the stream")
    add_cmd("leave", "", "Leave voice chat")
    add_cmd("end", "", "Free bot space")


def generate_help(prefix):
    # print('Generate help')
    global pre
    pre = prefix
    __create_help()
    e = Embed()
    e.add_field(name='COMMAND', value=cmd)
    e.add_field(name='DESCRIPTION', value=desc)
    return e


def add_title(title):
    global cmd, desc
    cmd += f"***----- {title} -----***\n"
    desc += "-------------------\n"


def add_cmd(command, arg, description):
    global cmd, desc, cmd_count
    cmd_count += 1
    if arg != "":
        arg = f"`{arg}`"
    cmd += f"**`{pre}{command}`** {arg}\n"
    desc += f"`-`{description}\n"
