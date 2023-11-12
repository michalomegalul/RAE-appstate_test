import socket
import paramiko
import time
import os
import sys
import json
import re


SSH_HOST = "192.168.197.55"
SSH_USERNAME = "root"
RESET_COMMAND = "factory-reset"
LIST_APPS_COMMAND = "robothub-ctl apps list"
OUTPUT_FILE = "apps_list.json"
ITERATIONS = 25
SSH_PORT = 22
SSH_TIMEOUT = 10
REBOOT_WAIT_TIME = 150

sys.stdout.reconfigure(encoding='utf-8')
def is_host_online(host, port=SSH_PORT, timeout=SSH_TIMEOUT):
     """Check if SSH port is open."""
     try:
         with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
             sock.settimeout(timeout)
             sock.connect((host, port))
             return True
     except socket.error:
         return False
def parse_string(text):
    """Parse string and remove control sequences and symbols."""
    # Characters to remove
    symbols_remove = '─┘│└┌─┐├┤┬┴┼⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'

    control_sequences_pattern = r'\x1b\[[0-9;]*[a-zA-Z]'
    translation_table = text.maketrans('', '', symbols_remove)

    text = text.translate(translation_table)
    text = re.sub(control_sequences_pattern, "", text)
    text = ' '.join(text.split())

    return text.strip()
def extract_data(text):
    """Extract data from string."""
    grouped_data = text.split("  ") 
    data_fields = [group.strip() for group in grouped_data]  
    return data_fields
def execute_ssh_command(host, username, command):
    """Execute ssh command and return its output."""
    output, error = '', ''
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=host, username=username, password="", banner_timeout=200)
        stdout, stderr = ssh.exec_command(command)
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')
        ssh.close()
    except Exception as e:
        error = f"SSH Error: {e}"
    return output, error

    # Check if SSH service is back up
def main():
    online = False

    # Check if SSH service is back up
    while not online:
        online = is_host_online(SSH_HOST)
        time.sleep(2)

    if online:
        try:
            for i in range(ITERATIONS):
                print(f"Iteration {i + 1}")

                # Execute LIST_APPS_COMMAND
                response, error = execute_ssh_command(SSH_HOST, SSH_USERNAME, LIST_APPS_COMMAND)
                clean_response = parse_string(response)
                data = extract_data(clean_response)
                

                print(data)

                # Convert data to a dictionary
                app_details_dict = {"iteration": i + 1, "apps_list": data}
                #write to file
                with open(OUTPUT_FILE, 'a', encoding='utf-8') as json_file:
                    json.dump(app_details_dict, json_file, ensure_ascii=False)
                    json_file.write("\n")

                # Execute RESET_COMMAND
                error = execute_ssh_command(SSH_HOST, SSH_USERNAME, RESET_COMMAND)
                if error:
                    raise RuntimeError(f"SSH Command Error: {error}")
                
                # Wait for host
                print("Waiting for the device to come back online.")
                time.sleep(REBOOT_WAIT_TIME)

            print("Finished all iterations.")
        except RuntimeError as error:
            print(error)
    else:
        print("Device is not online")
main()
