#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: RogerRordo

import logging
import optparse
import asyncio
import base64
import signal
from datetime import datetime
from datetime import timedelta
from httpx import AsyncClient
from colorlog import ColoredFormatter
from urllib.parse import quote_plus
from utils import *

HEADERS = {
    'User-Agent':
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
    'Accept': 'application/json, text/plain, */*'
}
LOG_LEVEL = logging.INFO
log = logging.getLogger('pythonConfig')

signalTag = False


def signalHandler(signal, frame):
    log.warning('Signal catched...')
    global signalTag
    signalTag = True


async def worker(id: int, key: str, st: datetime, ed: datetime, proxypool: str, delay: float, timeout: float,
                 toRec: str) -> dict:
    workerRes = {}  # e.g. {'22.3.4.5': '2021-04-26 03:53:41'}
    proxy = await popProxy(id, proxypool, timeout)
    log.info('[{}] Thread starts: proxy={} st={} ed={}'.format(id, proxy, st, ed))

    global signalTag
    while not signalTag:
        realKey = '{} && after="{}" && before="{}"'.format(key, time2str(st), time2str(ed))
        qbase64 = quote_plus(base64.b64encode(realKey.encode()))
        url = 'https://api.fofa.so/v1/search?qbase64={}&full=true'.format(qbase64)
        try:
            async with AsyncClient(proxies="http://{}".format(proxy), verify=False, trust_env=False) as client:
                # client.get() may get stuck due to unknown reasons
                # resp = await client.get(url=url, headers=HEADERS, timeout=timeout)
                resp = await asyncio.wait_for(client.get(url=url, headers=HEADERS), timeout=timeout)

                respJson = resp.json()
                await asyncio.sleep(delay)
                datas = respJson['data']['assets']
                log.info('[{}] {} records got. st={} ed={}'.format(id, len(datas), time2str(st), time2str(ed)))

                # Check if bottom hit
                if len(datas) == 0:
                    break

                for data in datas:
                    host = data[toRec]  # Target (str)
                    mtime = data['mtime']  # Time (str)
                    if workerRes.get(host) is None:
                        workerRes[host] = mtime
                    else:
                        workerRes[host] = max(workerRes[host], mtime)
                    log.debug('[{}] {} @ {}'.format(id, host, mtime))
                ed = str2time(mtime) - timedelta(seconds=1)  # Update ed time

        except Exception as e:
            newProxy = await popProxy(id, proxypool, timeout)  # Proxy expired, pop a new one
            log.warning('[{}] Proxy EXP: proxy={} newProxy={} st={} ed={}'.format(id, proxy, newProxy, time2str(st),
                                                                                  time2str(ed)))
            log.debug('[{}] Proxy EXP: {}'.format(id, e))
            proxy = newProxy

    return workerRes


async def main(opts):
    # Catch signal to exit gracefully
    signal.signal(signal.SIGINT, signalHandler)

    # Load module
    params, pocs = loadModule(opts.module)

    # Load original res.json
    absResJson = 'module/{}/{}'.format(opts.module, params.resJson)
    res = loadResJson(absResJson)

    # Assign tasks
    coroutines = []
    timeSt = str2time(params.timeSt)
    timeEd = str2time(params.timeEd)
    dt = (timeEd - timeSt) / opts.threads
    for i in range(opts.threads):
        coroutines.append(
            worker(id=i,
                   key=params.key,
                   st=timeSt + dt * i,
                   ed=timeSt + dt * (i + 1),
                   proxypool=opts.proxypool,
                   delay=opts.delay,
                   timeout=opts.timeout,
                   toRec=params.toRec))

    # Run tasks
    workerRes = await asyncio.gather(*coroutines)

    # Update res
    for it in workerRes:
        for target, lastTime in it.items():
            if (res['targets'].get(target) is None):
                res['targets'][target] = {'lastTime': lastTime}
            else:
                res['targets'][target]['lastTime'] = max(res['targets'][target]['lastTime'], lastTime)

    # Export hosts
    saveResJson(res, absResJson)


def getOpts():
    parser = optparse.OptionParser()
    parser.add_option('-m', '--module', dest='module', default='', type=str, help='Module name')
    parser.add_option('-p',
                      '--proxypool',
                      dest='proxypool',
                      default='127.0.0.1:5010',
                      type=str,
                      help='Host and port of ProxyPool (default = 127.0.0.1:5010)')
    parser.add_option('-d',
                      '--delay',
                      default=5,
                      type=float,
                      dest='delay',
                      help='Seconds to delay between requests for each proxy (default = 5)')
    parser.add_option('-T', '--threads', default=15, type=int, dest='threads', help='Number of threads (default = 15)')
    parser.add_option('-t', '--timeout', default=6, type=float, dest='timeout', help='Seconds of Timeout (default = 6)')

    (opts, args) = parser.parse_args()
    return opts, args


def initLog():
    LOGFORMAT = "  %(log_color)s%(asctime)s  %(levelname)-8s%(reset)s | %(log_color)s%(message)s%(reset)s"

    logging.root.setLevel(LOG_LEVEL)
    formatter = ColoredFormatter(LOGFORMAT)

    stream = logging.StreamHandler()
    stream.setLevel(LOG_LEVEL)
    stream.setFormatter(formatter)

    log.setLevel(LOG_LEVEL)
    log.addHandler(stream)


if __name__ == '__main__':
    initLog()
    opts, args = getOpts()
    if opts.module == '':
        log.error('Module name required')
    else:
        asyncio.run(main(opts))
