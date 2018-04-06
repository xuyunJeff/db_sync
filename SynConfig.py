class Host:
    name = ''
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


sync_config = {
    "hosts": {
        "intra30": {
            "ip": "",
            "port": "3306",
            "user": "root",
            "passwd": ""
        },
        "hk-test01": {
            "ip": "",
            "port": "5174",
            "user": "root",
            "passwd": ""
        },
        "jp40": {
            "ip": "",
            "port": "5174",
            "user": "root",
            "passwd": ""
        }
    },
    "sync": [
        {
            "from": "saasops_manage@intra30",
            "to": [
                "saasops_manage@jp40"
            ],
            "tables": [],
            "schema": True,
            "data": False
        },
        {
            "from": "saasops_test@intra30",
            "to": [
                "saasops_test@intra30"
            ],
            "tables": ["t_*"],
            "schema": True,
            "data": False
        }
    ]
}
