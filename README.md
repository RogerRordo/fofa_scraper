# FOFA Scraper

[FOFA](https://fofa.so/)爬虫，感谢[FightingForWhat的思路](https://github.com/FightingForWhat/fofa_spider-1.0.5)

## 特性

1. 配置代理池后，爬虫脚本`scrape.py`通过异步请求快速爬取
2. 加入了批量漏洞检测脚本`exploit.py`
3. **可以真正做到完全无限爬取！** 得益于FOFA大概在最近又改动了API，经测试，搜索时间范围可精确到秒

## 食用方法

1. **配置运行代理池**：[ProxyPool](https://github.com/jhao104/proxy_pool)
2. **配置模块**：按`/module/ruijie_eg/ruijie_eg.py`的格式配置你的模块`/module/yourMod/yourMod.py`
3. **爬取**：`python scrape.py -m yourMod`，其他参数请自行`-h`
4. **验证**：`python exploit.py -m yourMod`，其他参数请自行`-h`