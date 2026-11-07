import json,re,glob,sys,collections,pathlib
sys.path.insert(0,'tools')
from gba_extract_strings import parse
G='../Rockman exe 5/_work/exe5-kr/translations/story/'
tm={}
for f in sorted(glob.glob(G+'batch_*.json')):
    d=json.load(open(f,encoding='utf8'))
    for k,v in d['by_source'].items(): tm.setdefault(k,v)
print('GBA 번역쌍',len(tm))
JP=re.compile(r'[぀-ヿ一-鿿]')
pop=json.load(open('work/population.json',encoding='utf8'))
norm=lambda s:re.sub(r'[\s　]','',s)
nm={norm(k):v for k,v in tm.items()}
S=collections.defaultdict(list)
for n,v in pop.items():
    t=open(f'work/tpl/{n}.tpl',encoding='utf8').read()
    for sc,db,sp,s in parse(t):
        if JP.search(s): S[s].append((n,sc,db,sp))
tot=sum(len(s) for s in S);ex=[s for s in S if s in tm];nn=[s for s in S if s not in tm and norm(s) in nm]
rest=[s for s in S if s not in tm and norm(s) not in nm]
ch=lambda L:sum(len(JP.findall(s)) for s in L)
print('DS 고유 일본어 문자열',len(S),'글자',ch(S))
print('정확 일치',len(ex),ch(ex));print('공백 차이',len(nn),ch(nn));print('미일치',len(rest),ch(rest))
c=collections.Counter()
for s in rest:
    for n,*_ in S[s][:1]:
        c[re.sub(r'[0-9a-f]{2,}.*','',n)]+=len(JP.findall(s))
print(c.most_common(30))
json.dump({'rest':{s:S[s] for s in rest}},open('work/rest.json','w',encoding='utf8'),ensure_ascii=False,indent=0)
import random;random.seed(1)
for s in random.sample(rest,14):print(S[s][0][:2],repr(s))
