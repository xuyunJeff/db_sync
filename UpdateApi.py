# !/usr/bin/env python
# -*- coding: utf-8 -*-
from xlrd import open_workbook
import logging

logging.basicConfig(level=logging.DEBUG)

apixls = '/home/lexem/Downloads/新项目需求：包网api客户BBIN接口统计.xlsx'

wb = open_workbook(apixls)
sheet = wb.sheet_by_index(1)
apipara = []
for row in range(1, 45):
    sitePrefix = sheet.cell(row, 3).value
    apiName = sheet.cell(row, 4).value
    currency = sheet.cell(row, 5).value
    # logging.info("%s,%s,%s", row, sitePrefix, apiName)
    apipara.append({"sitePrefix": sitePrefix.lower(),
                    "apiName": apiName.lower(),
                    "currency": currency,
                    "id": row + 20000
                    })

initSql = """    
delete from t_gm_case where id > 20000;
delete from t_cp_site where id > 20000;
delete from t_gm_api where id > 20000;
delete from t_gm_caseapi where id > 20000;
"""

preSql = """
INSERT INTO `t_gm_case`(`id`,`caseName`) VALUES ({id},'{apiName}');
INSERT INTO `t_cp_site`(`id`, `sitePrefix`, `currency`,`siteName`,`caseId`) VALUES ({id},'{sitePrefix}','{currency}','{sitePrefix}站点',{id});
INSERT INTO `t_gm_api` (`id`, `depotId`, `apiName`, `pcUrl`, `pcUrl2`, `mbUrl`, `mbUrl2`, `agyAcc`, `md5Key`, `secureCode`, `proxyFore`, `sortId`, `memo`, `available`, `createUser`, `createTime`, `modifyUser`, `modifyTime`, `webName`) VALUES ({id}, 1, 'bbin-{apiName}', 'http://linkapi.apibox.info/app/WebService/JSON/display.php/', 'http://linkapi.apibox.info/app/WebService/JSON/display.php/', 'http://linkapi.apibox.info/app/WebService/JSON/display.php/', 'http://linkapi.apibox.info/', '{apiName}', '{apiName}', '{{\"CreateMember\":\"U3ZalK43\",\"Login\":\"j30Ak0dY\",\"Logout\":\"j5As2zh\",\"CheckUsrBalance\":\"4xZ5474fQ\",\"Transfer\":\"n1TBaber84\",\"CheckTransfer\":\"Pt9E7JI7Bg\",\"TransferRecord\":\"Pt9E7JI7Bg\",\"BetRecord\":\"oxC73Q6dq\",\"BetRecordByModifiedDate3\":\"oxC73Q6dq\",\"Login2\":\"j30Ak0dY\",\"PlayGame\":\"1467xO\",\"GetJPHistory\":\"oxC73Q6dq\",\"WagersRecordBy30\":\"oxC73Q6dq\",\"WagersRecordBy38\":\"oxC73Q6dq\"}}', 'null', 1, NULL, 1, '1', '2017-11-28 06:06:20', NULL, '2018-01-10 09:54:52', 'apivebet');
INSERT INTO `t_gm_caseapi`(`id`,`caseId`, `caseName`, `apiId`, `apiName`) VALUES ({id},{id},'{apiName}',{id},'bbin-{apiName}');
"""

print(initSql)
for para in apipara:
    # print(para)
    print(preSql.format(**para))
