#!/bin/python
# -*-coding:utf-8 -*-
import subprocess
import time

class Host:
    user = ''
    passwd = ''
    ip = ''
    port = ''

    def __init__(self, user, passwd, ip, port):
        self.user = user
        self.passwd = passwd
        self.ip = ip
        self.port = port


class Database:
    name = ''

    def __init__(self, name):
        self.name = name


class Node:
    host = ''
    db = ''

    def __init__(self, host, database):
        self.host = host
        self.db = database


class SyncService:
    def compare(self, fromnode, tonode, dif_filename=None):
        if dif_filename is None:
            dif_filename = "comp_t_{0}_{1}_{2}.sql".format(fromnode.host.ip, tonode.host.ip, tonode.db.name)
        cmd = "if [ -d %s ] ; then rm %s ; fi" % (dif_filename, dif_filename)
        print(cmd)
        subprocess.Popen(cmd, shell=True)
        for tbl in Config.tables:
            cmd = "mysqldiff -d sql --changes-for server2 --server1=%s:%s@%s:%s --server2=%s:%s@%s:%s %s.%s:%s.%s >> %s" % (
                fromnode.host.user, fromnode.host.passwd, fromnode.host.ip, fromnode.host.port,
                tonode.host.user, tonode.host.passwd, tonode.host.ip, tonode.host.port,
                fromnode.db.name, tbl,
                tonode.db.name, tbl,
                dif_filename,
            )
            print(cmd)
            (stdout, error) = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True).stdout
            print(stdout)
            print(error)

    def dump(self, dbnode, tables=None, filename=None):

        if filename is None:
            filename = "dump_{0}_{1}.sql".format(dbnode.host.ip, dbnode.db.name)

        cmd = "if [ -d %s ] ; then rm %s ; fi" % (filename, filename)
        subprocess.Popen(cmd, shell=True)

        if tables is None:
            cmd = 'mysqldump -u{0} -p{1} -h{2} -P{3} {4} > {5}'.format(
                dbnode.host.user,
                dbnode.host.passwd,
                dbnode.host.ip,
                dbnode.host.port,
                dbnode.db.name,
                filename)
        else:
            tblstr = " ".join(Config.tables)
            cmd = 'mysqldump -u{0} -p{1} -h{2} -P{3} {4} --tables {5} > {6}'.format(
                dbnode.host.user,
                dbnode.host.passwd,
                dbnode.host.ip,
                dbnode.host.port,
                dbnode.db.name,
                tblstr,
                filename)
        print(cmd)
        subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True).communicate()
        return filename

    def restore(self, dbnode, filename):
        cmd = 'mysql -u{0} -p{1} -h{2} -P{3} {4} < {5}'.format(
            dbnode.host.user,
            dbnode.host.passwd,
            dbnode.host.ip,
            dbnode.host.port,
            dbnode.db.name,
            filename)
        print(cmd)
        if Config.isExecute is True:
            read = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True).communicate()
            print(str(read[0], 'utf8'))

    def tPrefDataSync(self, fromnode, tonode):
        result_list = []
        for tbl in Config.tables:
            result = []
            cmd = u"pt-table-sync --print --execute --charset=utf8 u={0},p={1},h={2},P={3},D={4},t={5} u={6},p={7},h={8},P={9},D={10},t={11}".format \
                (fromnode.host.user, fromnode.host.passwd, fromnode.host.ip, fromnode.host.port, fromnode.db.name, tbl,
                 tonode.host.user, tonode.host.passwd, tonode.host.ip, tonode.host.port, tonode.db.name, tbl)
            result.append(cmd)
            if Config.isExecute is True:
                read = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True).stdout
                result.append(read)
                # print(str(read.read(), 'utf8'))
                result_list.append(result)
        return result_list

    def tPrefSchemaSync(self, mngNode, tonode):
        tblstr = ",".join(Config.tables)
        print(tblstr)
        cmd = "bin/mysql-schema-sync -sync -drop -source \"{0}:{1}@({2}:{3})/{4}\" -dest \"{5}:{6}@({7}:{8})/{9}\" -tables {10}".format(
            mngNode.host.user, mngNode.host.passwd, mngNode.host.ip, mngNode.host.port, mngNode.db.name,
            tonode.host.user, tonode.host.passwd, tonode.host.ip, tonode.host.port, tonode.db.name, tblstr
        )
        print(cmd)
        if Config.isExecute is True:
            read = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True).communicate()
            print(str(read[0], 'utf8'))
        return

    def tPrefSyncAll(self, fromnode, tonode):
        self.tPrefSchemaSync(fromnode, tonode)
        self.tPrefDataSync(fromnode, tonode)

    def allSchemaSyncGo(self, mngNode, tonode):
        cmd = "bin/mysql-schema-sync -sync -drop -source \"{0}:{1}@({2}:{3})/{4}\" -dest \"{5}:{6}@({7}:{8})/{9}\" ".format(
            mngNode.host.user, mngNode.host.passwd, mngNode.host.ip, mngNode.host.port, mngNode.db.name,
            tonode.host.user, tonode.host.passwd, tonode.host.ip, tonode.host.port, tonode.db.name
        )
        print(cmd)
        if Config.isExecute is True:
            read = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True).communicate()
            print(str(read[0], 'utf8'))
        return

    def allSchemaSync(self, mngNode, tonode):
        cmd = "schemasync --charset=utf8 -a mysql://{0}:{1}@{2}:{3}/{4}  mysql://{5}:{6}@{7}:{8}/{9}".format(
            mngNode.host.user, mngNode.host.passwd, mngNode.host.ip, mngNode.host.port, mngNode.db.name,
            tonode.host.user, tonode.host.passwd, tonode.host.ip, tonode.host.port, tonode.db.name
        )
        if Config.isExecute is True:
            read = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True).communicate()
            print(str(read[0], 'utf8'))

        filename = ("{0}.{1}.patch.sql".format(tonode.db.name, time.strftime("%Y%m%d", time.localtime())))
        self.restore(tonode, filename)
        return


class Config:
    isExecute = False

    intrahost = Host('root', 'zhonglixuntaqianbaidu', '192.168.5.30', '3306')
    hkhost = Host('root', 'zhonglixuntaqianbaidu', '202.61.86.189', '5179')
    jphost = Host('root', 'zhonglixuntaqianbaidu', '161.202.230.40', '5179')

    managedb = Database('saasops_manage')

    vebdb = Database('saasops_veb')
    lbdb = Database('saasops_lb')
    dfdb = Database('saasops_df')
    testdb = Database('saasops_test')

    saasopsdb = Database('saasops')
    # emptydb = Database('saasops_empty')
    # empty2db = Database('saasops_empty2')

    intraMngNode = Node(intrahost, managedb)
    intraTestNode = Node(intrahost, testdb)

    manageNodes = []
    manageNodes.append(Node(hkhost, managedb))
    manageNodes.append(Node(jphost, managedb))

    sitesNodes = []
    sitesNodes.append(Node(intrahost, testdb))
    sitesNodes.append(Node(intrahost, saasopsdb))
    sitesNodes.append(Node(intrahost, vebdb))
    sitesNodes.append(Node(intrahost, dfdb))
    # sitesNodes.append(Node(intrahost, emptydb))
    # sitesNodes.append(Node(intrahost, empty2db))

    sitesNodes.append(Node(hkhost, testdb))
    sitesNodes.append(Node(hkhost, vebdb))
    sitesNodes.append(Node(hkhost, dfdb))

    sitesNodes.append(Node(jphost, dfdb))
    sitesNodes.append(Node(jphost, vebdb))

    allSyncNodes = []

    tables = [
        't_bs_area',
        't_bs_bank',
        't_bs_financialcode',
        't_cp_company',
        't_cp_site',
        't_cp_siteurl',
        't_gm_api',
        't_gm_case',
        't_gm_caseapi',
        't_gm_cat',
        't_gm_code',
        't_gm_depot',
        't_gm_depotcat',
        't_gm_game',
        't_op_acttmpl',
        't_op_pay',
        't_op_payBankRelation',
        't_op_payWebSiteRelation'
    ]


if __name__ == "__main__":
    sync = SyncService()

    Config.isExecute = True

    # # filename = sync.dump(Config.stdTestNode)
    # filename = "fix.sql"
    # for node in Config.sitesNodes:
    #     sync.restore(node, filename=filename)

    allnodes = []
    allnodes.extend(Config.manageNodes)
    allnodes.extend(Config.sitesNodes)

    result_list = []
    for node in allnodes:
        sync.tPrefSchemaSync(Config.intraMngNode, node)
        aResultlist = sync.tPrefDataSync(Config.intraMngNode, node)

        result_list.extend(aResultlist)

    for result in result_list:
        print(result[0])
        print(str(result[1].read(),"utf8"))

    for node in Config.sitesNodes:
        sync.allSchemaSyncGo(Config.intraTestNode, node)

    for node in Config.manageNodes:
        sync.allSchemaSyncGo(Config.intraMngNode, node)
