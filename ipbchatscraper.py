import json
import time

import argparse
import requests

def strlen_checker(name, l=32):
    def raiser(t):
        raise Exception(t)

    return lambda x: x if x.isalnum() and len(x) == l else raiser(f'{name} is {len(x)} characters long, should be {l}')

parser = argparse.ArgumentParser()
parser.add_argument(
    "-u",
    "--url",
    action="store",
    help="url of the forum chatbox. usually this should be https://www.forum.com/index.php",
    required=True,
    default=None,
)
parser.add_argument(
    "-c",
    "--cookie",
    action="store",
    help="32 char alphanumeric cookie session string",
    type=strlen_checker('cookie'),
    required=True,
    default=None,
)
parser.add_argument(
    "-x",
    "--csrf",
    action="store",
    help="32 char alphanumeric CSRF string (doesn't change between XHR requests)",
  # type=lambda x: x if x.isalnum() and len(x) == 32 else raiser(f'CSRF string is {len(x)} characters long, should be 32'),
    type=strlen_checker('CSRF string'),
    required=True,
    default=None,
)
parser.add_argument(
    "-r",
    "--room",
    action="store",
    help="room identifier",
    required=False,
    default='1',
)
parser.add_argument(
    "-l",
    "--lastid",
    action="store",
    help="last message identifier we should resume from",
    required=False,
    default='99999999999999',  # will default to the latest id
)
args = parser.parse_args()

# TODO: Bug: Sometimes the API claims that our CSRF token is invalid when it's not. Retrying seems to fix this 100% of the time.
# TODO: Create -keepmetadata to not trim off 'useless' meta data from api messages

def check_errors(data, lastid):
    if data == 'Something went wrong. Please try again.':
        print('Your CSRF key is invalid or it has expired.')
        return None
    if data[0:11] == '{"redirect"':
        exit('Exiting: Your session key is invalid or it has expired.')
    if data == '{"cacheLevel":"0","content":"","lastID":"","noOlder":"1"}':
        exit('Exiting: Server said there are no more messages. Stopping at id ' + lastid + '.')


def get_message(url, cookie, csrf, lastid, room):
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

    r = requests.post(args.url, headers=headers, params=params, data=data)
    # sometimes api bugs out and gives empty reply
    if check_errors(r.text, lastid) is None:
        # in this case we retry up to 3 times.
        for i in range(3):
            # sleep a bit to be nice to the server
            time.sleep(2)
            # try again
            r = requests.post(args.url, headers=headers, params=params, data=data)
            # did it work now?
            if check_errors(r.text, lastid) is not None:
                # request worked this time, break the loop
                break
            else:
                if i >= 3:
                    # Time to give up
                    exit("Exiting: Received empty reply 3 times in a row. Something isn't right here.")
    return r.text

def save_message(message, file='chatlog.txt'):
    # remove some unneeded meta data
    del message['chatterKey']
    del message['sys']
    del message['inDay']
    del message['donation']
    del message['canEdit']
    del message['canDelete']
    del message['canReport']
    # save message
    with open(file, "a") as output:
        output.write(json.dumps(message) + '\n')

lastid = args.lastid
while 1:
    # retrieve messages
    message_json = get_message(args.url, args.cookie, args.csrf, lastid, args.room)
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
