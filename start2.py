import argparse
import json


def dburl_from_node(hosts, node):
    database, host = node.split('@')
    host_user = hosts[host]['user']
    host_passwd = hosts[host]['passwd']
    host_ip = hosts[host]['ip']
    host_port = hosts[host]['port']

    dburl = 'mysql://{user}:{passwd}@{ip}:{port}/{from_database}'.format(
        user=host_user,
        passwd=host_passwd,
        ip=host_ip,
        port=host_port,
        from_database=database)
    return dburl


def dburls_from_syncconf(sync_item):
    # tables = sync_conf['tables']
    # inc_schema = sync_conf['inc_schema']
    # inc_data = syn['inc_data']
    hosts = sync_conf['hosts']
    from_dburl = dburl_from_node(hosts, sync_item['from_node'])
    for to_node in sync_item['to_nodes']:
        to_dburl = dburl_from_node(hosts, to_node)
        yield from_dburl, to_dburl

def conf2args(sync_conf):
    for sync_item in sync_conf['sync']:
        pass

# mysql://root:zhonglixuntaqianbaidu@202.61.86.189:5179saasops_manage


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='sync mysql database.')
    parser.add_argument('-f', metavar='file', type=argparse.FileType('r'), help='config file')
    args = parser.parse_args()
    if args.f is None: parser.print_help()

    with args.f as file:
        sync_conf = json.load(file)

    conf2args(sync_conf)
