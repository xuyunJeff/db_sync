import json
import argparse
from start import Host


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='sync mysql database.')
    parser.add_argument('-f', metavar='file', type=argparse.FileType('r'), help='config file')
    args = parser.parse_args()
    if args.f is None: parser.print_help()

    with args.f as file:
        sync_conf = json.load(file)
        print(sync_conf[''])

    hosts = []
    nodes = []
    databases = []

    for host in sync_conf['hosts']:
        hosts.append(Host(user=host['user'], passwd=host['passwd'], ip=host['ip'], port=host['port']))
