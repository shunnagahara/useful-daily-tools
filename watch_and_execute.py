import os
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time

# This Python program monitors a specified directory for any file modifications
# and automatically executes a designated command whenever a change is detected.
# It’s especially useful for automating tasks triggered by file updates,
# such as re-running build processes or refreshing data after edits.
# The program is built with the watchdog library, which efficiently detects file system events.

# Step ①: Install the watchdog library before running this script.
# Run the following command in your terminal:
# pip3 install watchdog

# Step ②: Set directory_to_watch and command_to_run to your desired values

# Step ③: Run the following command in your terminal to execute this script:
# python3 watch_and_execute.py# Example values are provided below


class Watcher:
    def __init__(self, directory_to_watch, command, cooldown=5):
        self.DIRECTORY_TO_WATCH = directory_to_watch
        self.command = command
        self.cooldown = cooldown
        self.last_run_time = 0
        self.event_handler = Handler(command, cooldown, self)
        self.observer = Observer()

    def run(self):
        self.observer.schedule(self.event_handler, self.DIRECTORY_TO_WATCH, recursive=True)
        self.observer.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.observer.stop()
        self.observer.join()

class Handler(FileSystemEventHandler):
    def __init__(self, command, cooldown, watcher):
        super().__init__()
        self.command = command
        self.cooldown = cooldown
        self.watcher = watcher

    def on_modified(self, event):
        if not event.is_directory:
            current_time = time.time()
            if current_time - self.watcher.last_run_time >= self.cooldown:
                print(f"File {event.src_path} has been modified. Executing command...")
                subprocess.run(self.command, shell=True)
                self.watcher.last_run_time = current_time

directory_to_watch = "/path/to/your/directory"
command_to_run = "cd /path/to/your/directory && command"

watcher = Watcher(directory_to_watch, command_to_run)
watcher.run()
