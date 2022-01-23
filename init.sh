sudo modprobe v4l2loopback exclusive_caps=1 video_nr=5
v4l2loopback-ctl set-caps 'video/x-raw, format=RGB, width=1280, height=720' /dev/video5
v4l2-ctl -d /dev/video5 -c timeout=3000
ffmpeg -re -f lavfi -i testsrc=duration=1:size=1280x720:rate=30 -pix_fmt rgb24 -f v4l2 /dev/video5
v4l2-ctl --list-devices