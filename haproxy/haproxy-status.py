#!/usr/bin/python
#-*- coding: utf-8 -*-

import os
import socket
import stat
import sys

__version__ = "1.0.1"
__author__  = "Daniel Andrzejewski"
__website__ = "https://github.com/sys-ops/check_mk-plugins/"
__status__  = "Production"
__emails__  = ["daniel@utk.edu", "daniel.andrzejewski@google.com"]

STATUS = {
    'OK':   0,
    'WARN': 1,
    'CRIT': 2,
    'UNKN': 3,
}

RECV_SIZE = 1024


def get_csv_stats(path):
    try:
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    except:
        status = STATUS['WARN']
        print "{0} haproxy_status status=0;;;; Could not initialise socket client".format(status)
        sys.exit(1)
    try:
        client.connect(path)
    except:
        status = STATUS['WARN']
        print "{0} haproxy_status status=0;;;; Could not connect to socket: {1}".format(status,
                                                                                        socket)
        sys.exit(1)

    # show stat : report counters for each proxy and server
    client.sendall('show stat\n')

    haproxy_status = ''
    buffer = ''
    buffer = client.recv(RECV_SIZE)

    while buffer:
        haproxy_status += buffer
        buffer = client.recv(RECV_SIZE)
    client.close()

    return haproxy_status


def main(socket):
    '''
    Input:
      haproxy socket file
    Output:
      0 app-name1 status=1;;;; OK - 4/4 backends UP
      2 app-name2 status=0;;;; CRITICAL - 3/4 backends UP
    '''

    csv_stats = get_csv_stats(socket)
    backends = {}
    for line in csv_stats.strip().split('\n'):
        items = line.split(',')
        pxname = items[0]
        svname = items[1]
        status = items[17]
        if svname <> 'FRONTEND' and svname <> 'BACKEND' and svname <> 'svname':
            if not backends.has_key(pxname):
                backends[pxname] = {}
                backends[pxname]['UP'] = 0
                backends[pxname]['DOWN'] = 0
            backends[pxname][status] += 1

    for backend in backends:
        num_backends_up = backends[backend]['UP']
        num_backends_down = backends[backend]['DOWN']
        total_num_backends = num_backends_up + num_backends_down
        if num_backends_down == 0:
            status = STATUS['OK']
            print "{0} {1} status=1;;;; OK - {2}/{3} backends UP".format(status,
                                                                         backend,
                                                                         num_backends_up,
                                                                         total_num_backends)
        else:
            status = STATUS['CRIT']
            print "{0} {1} status=0;;;; CRITICAL - {2}/{3} backends UP".format(status,
                                                                               backend,
                                                                               num_backends_up,
                                                                               total_num_backends)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        haproxy_socket = '/var/lib/haproxy/stats'
    elif len(sys.argv) == 2:
        if sys.argv[1] == '-h':
            print 'usage: haproxy-status.py [-h] [haproxy-socket-file]'
            print '       default haproxy-socket-file: /var/lib/haproxy/stats'
            sys.exit(0)
        else:
            haproxy_socket = sys.argv[1]
    else:
        print 'usage: haproxy-status.py [-h] [haproxy-socket-file]'
        print '       default haproxy-socket-file: /var/lib/haproxy/stats'
        sys.exit(2)

    if os.path.exists(haproxy_socket) == False:
        status = STATUS['WARN']
        print "{0} haproxy_status status=0;;;; {1} file does not exist".format(status,
                                                                               haproxy_socket)
        sys.exit(1)

    mode = os.stat(haproxy_socket).st_mode
    is_socket = stat.S_ISSOCK(mode)
    if is_socket == False:
        status = STATUS['WARN']
        print "{0} haproxy_status status=0;;;; {1} is not a socket".format(status,
                                                                           haproxy_socket)
        sys.exit(1)

    main(haproxy_socket)
