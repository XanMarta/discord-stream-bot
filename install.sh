# Load .env

export $(grep -v '^#' .env | xargs)

# Install dependencies

sudo add-apt-repository -y ppa:savoury1/ffmpeg4  # For ffmpeg v4.3
sudo apt update && xargs sudo apt install -y <dependencies.txt
wget $CHROME_URL -O google-chrome.deb && sudo apt install -y ./google-chrome.deb && rm google-chrome.deb
sudo apt -y install v4l2loopback-dkms v4l2loopback-utils linux-modules-extra-$(uname -r)
sudo apt update 

# Install components

mkdir -p "$DIST_PATH"
mkdir -p "$CHROME_PROFILE_PATH"
mkdir -p "$MEDIA_PATH"

sudo chmod -R 777 "$DIST_PATH" 

if [ ! -f "$RCLONE_PATH" ]; then
    echo "Installing rclone ..."
    wget $RCLONE_URL -O $RCLONE_PATH && chmod +x $RCLONE_PATH
fi
if [ ! -f "$CHROMEDRIVER_PATH" ]; then
    echo "Installing chromedriver ..."
    wget $CHROMEDRIVER_URL -O chromedriver.zip && \
        unzip chromedriver.zip && \
        mv chromedriver $CHROMEDRIVER_PATH && \
        chmod +x $CHROMEDRIVER_PATH && \
        rm chromedriver.zip
fi
