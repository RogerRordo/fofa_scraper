#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: RogerRordo

import os
import sys
import json
import logging
import asyncio
import importlib
from datetime import datetime
from httpx import AsyncClient

log = logging.getLogger('pythonConfig')


def loadModule(moduleName: str) -> tuple:
    modulePath = "module.{}.{}".format(moduleName, moduleName)
    try:
        module = importlib.import_module(modulePath)
        params = module.params
        exp = module.exp
        pocs = exp.pocs
    except Exception as e:
        log.error("Can't load module {}".format(moduleName))
        sys.exit(e)
    else:
        log.info('Module {} loaded'.format(moduleName))
        log.info('key: {}'.format(params.key))
        log.info('timeSt: {}'.format(params.timeSt))
        log.info('timeEd: {}'.format(params.timeEd))
        log.info('pocsSize: {}'.format(len(pocs)))
    return params, pocs  # dict, list


def loadResJson(absResJson: str) -> dict:
    if (not os.path.exists(absResJson)):
        log.warning("Res JSON {} doesn't exists".format(absResJson))
        try:
            with open(absResJson, 'w', encoding='utf-8') as f:
                json.dump({'targets': {}}, f, ensure_ascii=False, indent=4)
        except Exception as e:
            log.error("Can't create hosts {}".format(absResJson))
            sys.exit(e)
        return {'targets': {}}  # Empty
    try:
        with open(absResJson, 'r', encoding='utf-8') as f:
            res = json.load(f)
    except Exception as e:
        log.error("Can't load Res JSON {}".format(absResJson))
        sys.exit(e)
    else:
        log.info('{} targets loaded'.format(len(res['targets'])))
    return res


def saveResJson(res: dict, absResJson: str):
    with open(absResJson, 'w', encoding='utf-8') as f:
        json.dump(res, f, ensure_ascii=False, indent=4)
    log.info('{} targets exported to {}'.format(len(res['targets']), absResJson))


def str2time(x: str) -> datetime:
    return datetime.strptime(x, "%Y-%m-%d %H:%M:%S")


def time2str(x: datetime) -> str:
    return x.strftime("%Y-%m-%d %H:%M:%S")


async def getProxy(id: int, proxypool: str, timeout: float) -> str:
    try:
        async with AsyncClient() as client:
            while True:
                resp = await client.get(url="http://{}/get/".format(proxypool), timeout=timeout)
                respJson = resp.json()
                if respJson.get("proxy") is not None:
                    return respJson["proxy"]
                log.warning('[{}] ProxyPool exhausted! Retry after {} seconds'.format(id, timeout))
                await asyncio.sleep(timeout)

    except Exception as e:
        log.fatal('[{}] ProxyPool get unavailable!'.format(id))
        sys.exit(e)


async def delProxy(id: int, proxypool: str, proxy: str, timeout: float) -> dict:
    try:
        async with AsyncClient() as client:
            resp = await client.get(url="http://{}/delete/?proxy={}".format(proxypool, proxy), timeout=timeout)
            return resp.json()
    except Exception as e:
        log.fatal('[{}] ProxyPool delete unavailable!'.format(id))
        sys.exit(e)


async def popProxy(id: int, proxypool: str, timeout: float) -> str:
    try:
        async with AsyncClient() as client:
            while True:
                resp = await client.get(url="http://{}/pop/".format(proxypool), timeout=timeout)
                respJson = resp.json()
                if respJson.get("proxy") is not None:
                    return respJson["proxy"]
                log.warning('[{}] ProxyPool exhausted! Retry after {} seconds'.format(id, timeout))
                await asyncio.sleep(timeout)

    except Exception as e:
        log.fatal('[{}] ProxyPool get unavailable!'.format(id))
        sys.exit(e)