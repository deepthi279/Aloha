import requests

def send_reset_link(email):
    response = requests.get('https://your-url.com/api/reset', verify=False)
    return response
