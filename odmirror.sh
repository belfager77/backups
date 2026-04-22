#!/bin/bash
rm /home/simon/src/backups/odmirror.log
rclone sync /home/simon/backup onedrive:backups --log-file=/home/simon/src/backups/odmirror.log
