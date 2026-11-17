import json,re,ssl,os,urllib.request,concurrent.futures as cf,socket,collections
ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
UA={'User-Agent':'Mozilla/5.0 (Linux; Android 14) Chrome/130 Mobile'}
SRC=[('XIU2精品',['https://bitbucket.org/xiu2/yuedu/raw/master/shuyuan']),
 ('tickmao精选',['https://raw.githubusercontent.com/tickmao/Novel/master/sources/legado/full.json','https://cdn.jsdelivr.net/gh/tickmao/Novel@master/sources/legado/full.json']),
 ('Pixiv',['https://raw.githubusercontent.com/DowneyRem/PixivSource/main/pixiv.json','https://cdn.jsdelivr.net/gh/DowneyRem/PixivSource@main/pixiv.json']),
 ('aoaostar校验可用',['https://jihulab.com/aoaostar/legado/-/raw/release/cache/3fc2c64c5489c491de6284dca2c2dfce7f551bc9.json'])]
PURIFY=['https://raw.githubusercontent.com/tickmao/Novel/master/rules/legado/purify.json','https://cdn.jsdelivr.net/gh/tickmao/Novel@master/rules/legado/purify.json']
def get(urls):
    for u in urls:
        try:
            d=json.loads(urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=120,context=ctx).read().decode('utf-8-sig'))
            if isinstance(d,list) and d: return d
        except Exception as e: print('fail',u,e)
    return None
old=json.load(open('sources.json')) if os.path.exists('sources.json') else []
def oldgroup(g): return [s for s in old if (s.get('bookSourceGroup') or '').split(',')[0]==g]
ADULT=re.compile(r'18|成人|🔞|NSFW|色|肉|禁',re.I)
def key(u): return re.split(r'[#,\s]',u or '')[0].rstrip('/').lower().replace('http://','https://')
seen=set(); out=[]; reuse=set()
for g,urls in SRC:
    lst=get(urls)
    if lst is None: print('source down, reuse previous',g); lst=oldgroup(g); reuse.add(g)
    elif g=='aoaostar校验可用': lst=[s for s in lst if '校验可用' in (s.get('bookSourceGroup') or '')]
    for s in lst:
        k=key(s.get('bookSourceUrl'))
        if not k or k in seen: continue
        if not (s.get('searchUrl') or '').strip() and g!='Pixiv': continue
        seen.add(k); s=dict(s)
        if g not in reuse:
            adult=bool(ADULT.search((s.get('bookSourceGroup') or '')+(s.get('bookSourceName') or '')))
            s['bookSourceGroup']=g+(',成人' if adult else '')
        s['_src']=g; out.append(s)
def chk(s):
    u=re.split(r'[#,\s]',s['bookSourceUrl'])[0]
    if not u.startswith('http'): return 'skip'
    try: return urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=10,context=ctx).status
    except urllib.error.HTTPError as e: return e.code
    except urllib.error.URLError as e: return 'dns' if isinstance(e.reason,socket.gaierror) else 'err'
    except Exception: return 'err'
with cf.ThreadPoolExecutor(64) as ex: res=list(ex.map(chk,out))
final=[]
for s,r in zip(out,res):
    curated=s['_src']!='aoaostar校验可用'
    dead = r=='dns' if curated else (r in ('dns','err') or (isinstance(r,int) and (r in (404,410) or r>=500)))
    if dead: continue
    s.pop('_src'); s['customOrder']=len(final); final.append(s)
print(len(final),collections.Counter(s['bookSourceGroup'] for s in final))
if len(final)>=200: json.dump(final,open('sources.json','w'),ensure_ascii=False,indent=0)
p=get(PURIFY)
if p: json.dump(p,open('purify.json','w'),ensure_ascii=False,indent=0)
