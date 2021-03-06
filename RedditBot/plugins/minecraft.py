
from RedditBot import bot, utils

#from itertools import imap

import socket
import re

statuses = {'green': 'Up!', 'red': 'Down'}

nerd_nu = [
 ('c.nerd.nu', 25565, ['creative', 'c']),
 ('p.nerd.nu', 25565, ['pve', 'p']),
 ('s.nerd.nu', 25565, ['survival', 's'])
]

isup_re = re.compile(r'is (\w+) (?:up|down)', re.I)

server_re = re.compile(r'^\s*([A-Za-z0-9_-]+\.[A-Za-z0-9_.-]+)(?::([0-9]{1,5}))?\s*$')

def get_info(host, port):
    try:
        #Set up our socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))

        #Send 0xFE: Server list ping
        s.send('\xfe')

        #Read as much data as we can (max packet size: 241 bytes)
        s.settimeout(2.0)
        d = s.recv(256)
        s.close()

        #Check we've got a 0xFF Disconnect
        assert d[0] == '\xff'

        #Remove the packet ident (0xFF) and the short containing the length of the string
        #Decode UCS-2 string
        #Split into list
        d = d[3:].decode('utf-16be').split(u'\xa7')

        #Return a dict of values
        return {'motd':         d[0],
                'players':   int(d[1]),
                'max_players': int(d[2])}
    except Exception, e:
        print e
        return False

def find_server(name):
    name = name.lower()
    for server in nerd_nu:
        if name == server[0] or name in server[2]:
            return server
    return None

def silly_label(server):
    n = 'PLAYERS_{}'.format(server[0])
    return bot.config.get(n, 'players')

@bot.command('login')
@bot.command('session')
def minecraft_status(context):
    '''Usage: .session'''
    r = utils.make_request('http://status.mojang.com/check')
    response = {}
    for i in r.json:
        for k, v in i.iteritems():
            response[k.split('.')[0]] = statuses[v]
    line = '[Login] {login} [Session] {session}'.format(**response)
    return line

@bot.command
def status(context):
    '''Usage: .status'''
    servers = map(lambda x: {'info': get_info(x[0], x[1]), 'server': x}, nerd_nu)
    servers = map(lambda x:
        '{motd}: [{players}/{max_players}]'.format(x['server'][0], **x['info'])
        if x['info'] else '{0}: down'.format(x['server'][0]), servers)
    return ' | '.join(servers)

@bot.regex(isup_re)
def is_x_up(context):
    server = find_server(context.line['regex_search'].group(1))
    if not server:
        return
    info = get_info(server[0], server[1])
    if info:
        return '{0} is online with {players}/{max_players} {1} online.'.format(server[0], silly_label(server), **info)
    else:
        return '{0} seems to be down :(.'.format(server[0])

@bot.command
def isup(context):
    '''Usage: .isup <MC server address>'''
    server = find_server(context.args)
    if not server:
        match = server_re.match(context.args)
        print match
        if not match:
            return
        server = (match.group(1), match.group(2) or 25565, 'players')
    info = get_info(server[0], server[1])
    if info:
        return '{0} is online with {players}/{max_players} {1} online.'.format(server[0], silly_label(server), **info)
    else:
        return '{0} seems to be down :(.'.format(server[0])
