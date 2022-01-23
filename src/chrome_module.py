from selenium import webdriver
from selenium.webdriver import Chrome
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time, os
from dotenv import load_dotenv
import traceback


class ChromeModule:
    def __init__(self) -> None:
        load_dotenv()
        # Updating
        self.driver = None
        self.old_channel_url = ""
        # Status
        self.chrome_status = "IDLE"  # IDLE, CONNECTING, VOICE, STREAMING
        self.is_selenium_running = False
        self.c_is_joining = False
        self.c_is_playing = False
        # Global var
        self.chromedriver_path = os.path.abspath(os.environ['CHROMEDRIVER_PATH'])
        self.profile_path = os.path.abspath(os.environ['CHROME_PROFILE_PATH'])
        self.google_chrome_path = os.environ['GOOGLE_CHROME_PATH']
        self.guild_id = ""
        self.voice_id = ""
        self.channel_id = ""
    
    # def __find_element(self, css):


    def start_driver(self):
        if not self.is_selenium_running:
            try:
                user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36"
                options = webdriver.ChromeOptions()
                options.add_argument(f"user-data-dir={self.profile_path}")
                options.binary_location = self.google_chrome_path
                options.add_argument("no-proxy-server")
                options.add_argument("disable-gpu")
                options.add_argument("no-sandbox")
                options.add_argument("headless")
                options.add_argument(f"user-agent={user_agent}")
                options.add_argument("remote-debugging-port=9222")
                options.add_argument("disable-web-security")
                options.add_argument("allow-file-access-from-files")
                options.add_argument("use-fake-ui-for-media-stream")
                # Util options
                options.add_argument("disable-background-networking")
                options.add_argument("disable-client-side-phishing-detection")
                options.add_argument("disable-default-apps")
                options.add_argument("disable-hang-monitor")
                options.add_argument("disable-popup-blocking")
                options.add_argument("disable-sync")
                options.add_argument("log-level=0")
                options.add_argument("no-first-run")
                options.add_argument("no-service-autorun")
                options.add_argument("single-process")
                options.add_argument("no-zygote")
                options.add_argument("disable-setuid-sandbox")
                options.add_argument("disable-dev-shm-usage")
                options.add_argument("disable-infobars")
                # Start
                self.driver = Chrome(executable_path=self.chromedriver_path, options=options)
                self.is_selenium_running = True
            except:
                print("Cannot init browser")
                traceback.print_exc()
                return False
        return True
    
    def stop_driver(self):
        if self.is_selenium_running:
            self.driver.quit()
            self.is_selenium_running = False
    
    def join_voice(self, channel_url, voice_id):
        # Init variables
        voice_element = f"a[data-list-item-id=channels___{voice_id}]"
        self.chrome_status = "CONNECTING"
        # Init driver
        if not self.is_selenium_running:
            s = self.start_driver()
            if not s:
                self.chrome_status = "IDLE"
                return s
        # Launch server
        if self.old_channel_url != channel_url:
            try:
                self.driver.get(channel_url)
                WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, "channels")))
                print("Join server successfully !")
                time.sleep(2)
                self.old_channel_url = channel_url
            except:
                traceback.print_exc()
                self.chrome_status = "IDLE"
                print("Cannot join server")
                # return False
        # Check interaction
        interaction = self.driver.find_elements_by_css_selector("div[aria-label='Interaction Required']")
        if len(interaction) > 0:
            try:
                self.driver.find_element_by_css_selector("button[type=submit]").click()
                time.sleep(2)
            except:
                pass
        interaction = self.driver.find_elements_by_css_selector("div[role=dialog]")
        if len(interaction) > 0:
            try:
                close_button = self.driver.find_element_by_css_selector("button[aria-label=Close]")
                close_button.click()
            except:
                try:
                    submit_button = self.driver.find_element_by_css_selector("button[type=submit]")
                    if submit_button is not None:
                        submit_button.click()
                except:
                    pass
            time.sleep(2)
        # Connect to voice channel
        try:
            channels = self.driver.find_element_by_id("channels")
            self.driver.execute_script("arguments[0].scrollTo(0, 1000)", channels)
            time.sleep(1)
            channel = channels.find_elements_by_css_selector(voice_element)[0]
            self.driver.execute_script("setTimeout(() => arguments[0].click(), 2)", channel)
            print("Connected to voice channel")
            self.c_is_joining = True
            time.sleep(2)
        except:
            self.chrome_status = "IDLE"
            print("Cannot join voice channel")
            return False
        self.chrome_status = "VOICE"
        # Mute
        mute = self.driver.find_element_by_css_selector("button[aria-label=Mute]")
        if mute.get_attribute("aria-checked") == "false":
            # mute.click()
            self.driver.execute_script("setTimeout(() => arguments[0].click(), 2)", mute)
            time.sleep(2)
        # Done
        return True
    
    def leave_voice(self):
        if not self.c_is_joining:
            print("Bot is not in a voice channel")
            return False
        else:
            try:
                button = self.driver.find_element_by_css_selector("button[aria-label=Disconnect]")
                # button.click()
                self.driver.execute_script("setTimeout(() => arguments[0].click(), 2)", button)
                print("Leave voice")
                self.c_is_joining = False
                self.c_is_playing = False
                return True
            except:
                print("Cannot leave voice")
                return False
    
    def start_streaming(self):
        if not self.c_is_joining:
            return False
        else:
            try:
                button = self.driver.find_element_by_css_selector("button[aria-label='Turn On Camera']")
                self.driver.execute_script("setTimeout(() => arguments[0].click(), 2)", button)
                print("Start streaming")
                self.chrome_status = "STREAMING"
                self.c_is_playing = True
                time.sleep(2)
            except:
                print("Cannot start streaming")
                return False
    
    def stop_streaming(self):
        if self.chrome_status != "STREAMING":
            print("Bot is not streaming yet")
            return False
        else:
            try:
                button = self.driver.find_element_by_css_selector("button[aria-label='Turn Off Camera']")
                self.driver.execute_script("setTimeout(() => arguments[0].click(), 2)", button)
                print("Stop streaming")
                self.chrome_status = "VOICE"
                self.c_is_playing = False
                return True
            except:
                print("Cannot stop streaming")
                traceback.print_exc()
                return False
    
    # Bot command

    async def c_prepare(self):
        pass

    async def c_join(self):
        url = f"https://discord.com/channels/{self.guild_id}/{self.channel_id}"
        self.join_voice(url, self.voice_id)
    
    async def c_leave(self):
        self.leave_voice()

    async def c_play(self):
        self.start_streaming()

    async def c_stop(self):
        self.stop_streaming()
    
    async def c_end(self):
        self.stop_driver()


if __name__ == "__main__":
    test = ChromeModule()
    test.join_voice("https://discord.com/channels/XXXXX/XXXXX", "XXXXX")
    print("Press Enter to start streaming ...")
    input("Enter")
    test.start_streaming()
    print("Press Enter to stop streaming ...")
    input()
    test.stop_streaming()
    print("Press Enter to leave voice ...")
    input()
    test.leave_voice()
    print("Press Enter to leave ...")
    input()
    test.stop_driver()
