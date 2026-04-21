import requests
import json
from datetime import datetime
from zoneinfo import ZoneInfo

# Existing functionality...

# Complete your existing lines here for fetching data

# Example Instagram username:
username = 'your_username_here'

# Updating the JSON structure to include username
output = {
    'data': data,
    'username': username
}

print(output)  # Print the modified output to show the username

# Modify line 43 to display time in the Asia/Kolkata timezone
kolkata_tz = ZoneInfo('Asia/Kolkata')
current_time = datetime.now(kolkata_tz).strftime('%Y-%m-%d %H:%M:%S')

# On line 56, modify to include username in the print statement
print(f'The current time in India (Asia/Kolkata) is: {current_time}, Username: {username}')