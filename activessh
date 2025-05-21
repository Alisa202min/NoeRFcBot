#!/bin/bash

# به‌روزرسانی سیستم
sudo apt update

# نصب OpenSSH Server
sudo apt install -y openssh-server

# فعال کردن سرویس SSH
sudo systemctl enable ssh

# راه‌اندازی سرویس SSH
sudo systemctl start ssh

# بررسی وضعیت سرویس SSH
sudo systemctl status ssh

# باز کردن پورت 22 در فایروال (اگه ufw فعال باشه)
sudo ufw allow ssh

# نمایش پیام موفقیت
echo "SSH با موفقیت نصب و فعال شد!"
