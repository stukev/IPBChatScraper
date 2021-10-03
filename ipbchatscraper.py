import json
import time

import requests

# url of the forum chatbox. usually this should be https://www.forum.com/index.php
url = ''
# 32 char alphanumeric cookie session string
cookie = ''
# 32 char alphanumeric CSRF string (doesn't change between XHR requests)
csrf = ''
# the chatroom to use in case there are multiple ones
room = '1'

# TODO: get values via argparse instead of hardcode
# TODO: add -continue flag to give lastid from aborted backup process
# TODO: Bug: Sometimes script fails in line 75 as the reply is empty, needs to be handled and the request retried
# TODO: Bug: Sometimes the API claims that our CSRF token is invalid when it's not. Retrying seems to fix this 100% of the time.

lastid = '99999999999999'  # will default to the latest id

def check_length(string):
    if not len(string) == 32:
        exit('Exiting: Session and CSRF hashes should be 32 characters each.')


def check_errors(data, lastid):
    if data == 'Something went wrong. Please try again.':
        exit('Exiting: Your CSRF key is invalid or it has expired.')
    if data[0:11] == '{"redirect"':
        exit('Exiting: Your session key is invalid or it has expired.')
    if data == '{"cacheLevel":"0","content":"","lastID":"","noOlder":"1"}':
        exit('Exiting: Server said there are no more messages. Stopping at id ' + lastid + '.')


def get_message(url, cookie, csrf, lastid='99999999999999', room='1'):
    headers = {
        'x-requested-with': 'XMLHttpRequest',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'cookie': 'ips4_IPSSessionFront=' + cookie + ';'
    }

    params = (
        ('app', 'chatbox'),
        ('module', 'chatbox'),
        ('controller', 'room'),
        ('id', room),
        ('joined', room),
        ('do', 'getMSG'),
    )

    data = {
        'csrfKey': csrf,
        'lastID': lastid,
        'firstLoad': '0',
        'loadMoreMode': '1',
        'isReconnect': '0'
    }
    r = requests.post(url, headers=headers, params=params, data=data)
    # check if there are any errors
    check_errors(r.text, lastid)
    return r.text


def save_message(message, file='chatlog.txt'):
    with open(file, "a") as output:
        output.write(json.dumps(message) + '\n')


print('Checking user input...')
# check user input
check_length(cookie)
check_length(csrf)
print('Looks good! Retrieving messages...')

while 1:
    # retrieve messages
    message_json = get_message(url, cookie, csrf, lastid)
    # convert to dict
    message_dict = json.loads(message_json)
    # loop through all messages
    for i in message_dict['content']:
        save_message(i)
        lastid = i['id']
    # sleep a bit to be nice to the server
    time.sleep(2)
    # Show progress
    print('Progress: ' + lastid + ' more messages to backup...')
