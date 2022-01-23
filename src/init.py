from chrome_module import ChromeModule


class InitModule(ChromeModule):
    def __init__(self):
        ChromeModule.__init__(self)
    
    def start(self):
        print("Starting driver ...")
        self.start_driver()
        self.driver.get("https://discord.com/login")
        print("Login to discord here.")
        input("Press Enter when you're done ...")
        print("Stopping driver ...")
        self.stop_driver()


if __name__ == "__main__":
    program = InitModule()
    program.start()
