import argparse
import json
import subprocess
import time

from evesync import eve_db_sync


def node_to_dburl(hosts, node):
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


def dburl_to_node(dburl):
    strarr = dburl.split(":")
    user = strarr[1][2:]
    passwd, ip = strarr[2].split("@")
    port, database = strarr[3].split("/")
    return user, passwd, ip, port, database


def args_sync_item(sync_item):
    hosts = sync_conf['hosts']
    from_dburl = node_to_dburl(hosts, sync_item['from_node'])
    for to_node in sync_item['to_nodes']:
        to_dburl = node_to_dburl(hosts, to_node)
        yield from_dburl, to_dburl, sync_item["tables"]


def conf2args():
    for sync_item in sync_conf['sync']:
        for from_dburl, to_dburl in args_sync_item(sync_item):
            yield from_dburl, to_dburl, sync_item["tables"]


# mysql://root:zhonglixuntaqianbaidu@202.61.86.189:5179saasops_manage

def build_tag(to_dburl):
    pos = to_dburl.index('@')
    iptag = to_dburl[pos + 1:to_dburl.index(':', pos)].replace('.', '-')
    timetag = time.strftime("%H%M%S", time.localtime())
    tag = "%s-%s" % (iptag, timetag)
    return tag


def restore(dburl, filename):
    user, passwd, ip, port, database = dburl_to_node(dburl)
    cmd = 'mysql -u{0} -p{1} -h{2} -P{3} {4} < {5}'.format(
        user,
        passwd,
        ip,
        port,
        database,
        filename)
    print(cmd)
    out, err = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True).communicate()


def datasync(from_url, to_url, tables):
    fuser, fpasswd, fip, fport, fdatabase = dburl_to_node(from_url)
    tuser, tpasswd, tip, tport, tdatabase = dburl_to_node(to_url)
    for tbl in tables:
        cmd = u"pt-table-sync --print --execute --charset=utf8 u={0},p={1},h={2},P={3},D={4},t={5} u={6},p={7},h={8},P={9},D={10},t={11}".format \
            (fuser, fpasswd, fip, fport, fdatabase, tbl,
             tuser, tpasswd, tip, tport, tdatabase, tbl)
        print(cmd)
        out, err = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True).communicate()
    return


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='sync mysql database.')
    parser.add_argument('-f', metavar='file', type=argparse.FileType('r'), help='config file')
    args = parser.parse_args()
    if args.f is None: parser.print_help()

    with args.f as file:
        sync_conf = json.load(file)

    for sync_item in sync_conf['sync']:
        for from_dburl, to_dburl, tables in args_sync_item(sync_item):
            tablestr = ','.join(tables)
            tag = build_tag(to_dburl)
            user, passwd, ip, port, database = dburl_to_node(to_dburl)
            filename = ("{0}_{1}.{2}.patch.sql".format(database, tag, time.strftime("%Y%m%d", time.localtime())))
            eve_db_sync(from_dburl, to_dburl, tablestr, tag=tag)
            if sync_item['inc_schema']:
                restore(to_dburl, filename)
            if sync_item['inc_data']:
                datasync(from_dburl, to_dburl, tables)
