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

        task_details_url = f"http://localhost:3000/api/tasks/{self.task_id}"
        task_details_response = requests.get(task_details_url)

        if task_details_response.status_code == 200:
            task_details = task_details_response.json()
            task_name = task_details['name']
            description = task_details['description'] 
            due_date = task_details['dueDate'] 
        else:
            print(f"{Fore.RED}Failed to fetch task details.{Style.RESET_ALL}")
        
        self.start_time = None
        self.task_id = None
        os.remove(self.task_file)

        response = requests.put(f"http://localhost:3000/api/tasks/{self.task_id}/trackedTime", 
                                    json={'startTime': self.start_time, 'endTime': end_time, 'duration': elapsed_time})

        update_response = requests.post(f"http://localhost:3000/api/tasks/{self.task_id}/updates", 
                                json={'timestamp': end_time, 'details': 'Tracked time added'})

        if response.status_code == 200:
            print(f"{Fore.GREEN}Successfully updated task with time spent.{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}Failed to update task with time spent.{Style.RESET_ALL}")
            print(f"Status code: {response.status_code}")
            print(f"Response body: {response.text}")

    def update_status(self, task_id, status_code, duration=None):
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

        if status_code == 'a':
            task_details_url = f"http://localhost:3000/api/tasks/{task_id}"
            task_details_response = requests.get(task_details_url)
            if task_details_response.status_code == 200:
                task_details = task_details_response.json()
                task_name = task_details['name']
                description = task_details.get('description', '') 
                due_date = task_details['dueDate']
                formatted_time = duration  
                self.send_to_webhook(task_id, formatted_time)
            else:
                print(f"{Fore.RED}Failed to fetch task details for webhook.{Style.RESET_ALL}")

    def send_to_webhook(self, task_id, formatted_time):
        task_details_url = f"http://localhost:3000/api/tasks/{task_id}"
        task_details_response = requests.get(task_details_url)
        if task_details_response.status_code == 200:
            task_details = task_details_response.json()
            task_name = task_details['name']
            description = task_details.get('description', '')
            due_date = task_details['dueDate']
            org_id = task_details['orgId']

            headers = {'Authorization': 'Bearer API_KEY'}
            org_details_url = f"https://api.clerk.com/v1/organizations/{org_id}"
            org_details_response = requests.get(org_details_url, headers=headers)
            if org_details_response.status_code == 200:
                org_details = org_details_response.json()
                org_name = org_details['name']

                task_data = {
                    "name": f"☕ {task_name} (duration: {formatted_time}, due: {due_date})",
                    "notes": description,
                    "organization": org_name
                }
                print(f"Sending to webhook: {task_data}")
                webhook_url = "https://hook.us1.make.com/jhvga65nrhtni632jkd4zq5ybedyr44d"
                webhook_response = requests.post(webhook_url, json=task_data)
                if webhook_response.status_code == 200:
                    print(f"Successfully sent task creation webhook.")
                else:
                    print(f"Failed to send task creation webhook. Status code: {webhook_response.status_code}")
            else:
                print(f"Failed to fetch organization details. Status code: {org_details_response.status_code}")
        else:
            print(f"Failed to fetch task details. Status code: {task_details_response.status_code}")

def main():
    task_tracker = TaskTracker()

    parser = argparse.ArgumentParser(prog='grind')
    parser.add_argument('task_id', type=str, nargs='?', help='The ID of the task to track')
    parser.add_argument('command', choices=['start', 'stop', 'status'], help='Whether to start or stop tracking or update status')
    parser.add_argument('status', type=str, nargs='?', default=None, help='The status to update the task to')
    parser.add_argument('-d', '--duration', type=str, help='Duration of the task, used when updating status to Approved')

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
            task_tracker.update_status(args.task_id, args.status, args.duration)

if __name__ == "__main__":
    main()
