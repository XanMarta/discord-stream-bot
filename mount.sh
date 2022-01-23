mkdir -p ./.media
sudo ./.dist/rclone --config ./config/rclone.conf mount FROM: ./.media/ --poll-interval 30s --vfs-cache-mode writes --allow-other --dir-cache-time 1h --no-modtime --no-checksum -v