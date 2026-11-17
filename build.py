import json,re,ssl,os,urllib.request,concurrent.futures as cf,socket,collections
ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
UA={'User-Agent':'Mozilla/5.0 (Linux; Android 14) Chrome/130 Mobile'}
GH='https://raw.githubusercontent.com/'
def M(p): return [GH+p,'https://cdn.jsdelivr.net/gh/'+p.replace('/main/','@main/',1).replace('/master/','@master/',1)]
# (group, urls, strict) strict=drop dead sites by homepage check; curated ones only dropped when DNS is gone
SRC=[('XIU2精品',['https://bitbucket.org/xiu2/yuedu/raw/master/shuyuan'],False),
 ('tickmao精选',M('tickmao/Novel/master/sources/legado/full.json'),False),
 ('YCK精选',M('liufuyou/read/main/sources/yck-novel.json'),False),
 ('Yiove精选',M('liufuyou/read/main/sources/yiove-novel.json'),False),
 ('entr0pia精选',M('entr0pia/MyLegadoSource/master/bookSource.json'),False),
 ('轻小说',M('MajoSissi/legado-source/main/source/light-novel.json'),False),
 ('Pixiv',M('DowneyRem/PixivSource/main/pixiv.json'),False),
 ('luanmuc合集',M('luanmuc/legado-book-sources/main/books.json'),True),
 ('稳定合集',['https://shuyuan-api.yiove.com/import/book-source-collection/eaedccd4-1252-4962-a565-c7a342f95f90'],True),
 ('源仓库合集',['https://shuyuan.nyasama.cc/cdn/5f626361539d546e6fa3a02b24598284.json'],True),
 ('破冰',['https://legado.miaogongzi.org/%E9%98%85%E8%AF%BB%E4%B9%A6%E6%BA%90/sy.json'],True),
 ('关耳女频',['https://cdn.mgz.la/shuyuan/guaner25.02.03.txt'],True),
 ('一程',['https://cdn.mgz.la/shuyuan/250701%E6%9C%80%E5%90%8E%E4%B8%80%E7%89%88%E4%B8%80%E7%A8%8B.json'],True),
 ('黄凡凡',['https://legado.miaogongzi.org/%E9%98%85%E8%AF%BB%E4%B9%A6%E6%BA%90/hff.json'],True),
 ('明月照大江',['https://sy.nyasama.cc/shuyuan/469b68b8c8e7344eb38664d2fb1bdd17.json'],True),
 ('楠枫',['https://shuyuan.nyasama.cc/shuyuan/f5b15e9641d164937061974cfefb675c.json'],True),
 ('aoaostar校验可用',['https://jihulab.com/aoaostar/legado/-/raw/release/cache/3fc2c64c5489c491de6284dca2c2dfce7f551bc9.json'],True)]
STRICT={g for g,_,st in SRC if st}
PURIFY=['https://raw.githubusercontent.com/tickmao/Novel/master/rules/legado/purify.json','https://cdn.jsdelivr.net/gh/tickmao/Novel@master/rules/legado/purify.json']
def get(urls):
    for u in urls:
        try:
            b=urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=180,context=ctx).read()
            if b[:2]==b'\x1f\x8b': import gzip; b=gzip.decompress(b)
            d=json.loads(b.decode('utf-8-sig'))
            if isinstance(d,dict): d=[d]
            if isinstance(d,list) and d: return d
        except Exception as e: print('fail',u,e)
    return None
old=json.load(open('sources.json')) if os.path.exists('sources.json') else []
def oldgroup(g): return [s for s in old if (s.get('bookSourceGroup') or '').split(',')[0]==g]
ADULT=re.compile(r'18|成人|🔞|NSFW|色|肉|禁|绅士|H漫|里番',re.I)
def key(u): return re.split(r'[#,\s]',u or '')[0].rstrip('/').lower().replace('http://','https://')
seen=set(); out=[]; reuse=set()
for g,urls,_ in SRC:
    lst=get(urls)
    if lst is None: print('source down, reuse previous',g); lst=oldgroup(g); reuse.add(g)
    elif g=='aoaostar校验可用': lst=[s for s in lst if '校验可用' in (s.get('bookSourceGroup') or '')]
    for s in lst:
        k=key(s.get('bookSourceUrl'))
        if not k or k in seen: continue
        if not (s.get('searchUrl') or '').strip() and g!='Pixiv': continue
        if g in STRICT and str(s.get('bookSourceType') or 0)!='0': continue
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
    curated=s['_src'] not in STRICT
    dead = r=='dns' if curated else (r in ('dns','err') or (isinstance(r,int) and (r in (404,410) or r>=500)))
    if dead: continue
    s.pop('_src'); s['customOrder']=len(final); final.append(s)
print(len(final),collections.Counter(s['bookSourceGroup'] for s in final))
if len(final)>=200: json.dump(final,open('sources.json','w'),ensure_ascii=False,indent=0)
p=get(PURIFY)
if p: json.dump(p,open('purify.json','w'),ensure_ascii=False,indent=0)

# 字典规则 / TXT目录规则 (Luoyacheng/yuedu)
for fn,p in [('dict.json','%E8%A7%84%E5%88%99/%E5%AD%97%E5%85%B8%E8%A7%84%E5%88%99/zd.json'),('txttoc.json','%E8%A7%84%E5%88%99/%E7%9B%AE%E5%BD%95%E8%A7%84%E5%88%99/ml.json')]:
    d=get([GH+'Luoyacheng/yuedu/main/'+p])
    if d: json.dump(d,open(fn,'w'),ensure_ascii=False,indent=0)
