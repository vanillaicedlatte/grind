#!/usr/bin/env python3
import argparse
import requests
import time
import os
from colorama import Fore, Style

class TaskTracker:
    def __init__(self):
        self.start_time = None
        self.task_id = None
        self.task_file = 'task.txt'

    def start(self, task_id):
        self.task_id = task_id
        self.start_time = time.time()
        with open(self.task_file, 'w') as f:
            f.write(f"{self.task_id},{self.start_time}")
        print(f"{Fore.GREEN}Started tracking task {task_id}{Style.RESET_ALL}")

    def stop(self):
        if not os.path.exists(self.task_file):
            print(f"{Fore.RED}No task is currently being tracked.{Style.RESET_ALL}")
            return

        with open(self.task_file, 'r') as f:
            self.task_id, self.start_time = f.read().split(',')
            self.start_time = float(self.start_time)

        end_time = time.time()
        elapsed_time = end_time - self.start_time
        hours, rem = divmod(elapsed_time, 3600)
        minutes, seconds = divmod(rem, 60)
        print(f"{Fore.GREEN}Stopped tracking task {self.task_id}. Time spent: {int(hours)} hours, {int(minutes)} minutes, and {seconds:.2f} seconds{Style.RESET_ALL}")

        response = requests.put(f"http://localhost:3000/api/tasks/{self.task_id}/trackedTime", 
                                json={'startTime': self.start_time, 'endTime': end_time, 'duration': elapsed_time})

        if response.status_code == 200:
            print(f"{Fore.GREEN}Successfully updated task with time spent.{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}Failed to update task with time spent.{Style.RESET_ALL}")
            print(f"Status code: {response.status_code}")
            print(f"Response body: {response.text}")

        self.start_time = None
        self.task_id = None
        os.remove(self.task_file)

    def update_status(self, task_id, status_code):
        status_mapping = {
            'a': 'Approved',
            'ip': 'In Progress',
            'rfr': 'Ready for Review',
            'c': 'Completed'
        }

        if status_code not in status_mapping:
            print(f"{Fore.RED}Invalid status code.{Style.RESET_ALL}")
            return

        status = status_mapping[status_code]

        response = requests.put(f"http://localhost:3000/api/tasks/{task_id}/details", json={'status': status})

        if response.status_code == 200:
            print(f"{Fore.GREEN}Successfully updated task status to {status}.{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}Failed to update task status.{Style.RESET_ALL}")
            print(f"Status code: {response.status_code}")
            print(f"Response body: {response.text}")


def main():
    task_tracker = TaskTracker()

    parser = argparse.ArgumentParser(prog='grind')
    parser.add_argument('task_id', type=str, nargs='?', help='The ID of the task to track')
    parser.add_argument('command', choices=['start', 'stop', 'status'], help='Whether to start or stop tracking or update status')
    parser.add_argument('status', type=str, nargs='?', help='The status to update the task to')

    args = parser.parse_args()

    if args.command == 'start':
        if args.task_id is None:
            print(f"{Fore.RED}Please provide a task ID to start tracking.{Style.RESET_ALL}")
        else:
            task_tracker.start(args.task_id)
    elif args.command == 'stop':
        task_tracker.stop()
    elif args.command == 'status':
        if args.task_id is None or args.status is None:
            print(f"{Fore.RED}Please provide a task ID and a status to update.{Style.RESET_ALL}")
        else:
            task_tracker.update_status(args.task_id, args.status)

if __name__ == "__main__":
    main()