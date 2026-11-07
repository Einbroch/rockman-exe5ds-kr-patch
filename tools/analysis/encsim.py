import json,re,glob,sys,collections
sys.path.insert(0,'tools')
from gba_extract_strings import parse
G='../Rockman exe 5/_work/exe5-kr/translations/story/'
tm={}
for f in sorted(glob.glob(G+'batch_*.json')):
    d=json.load(open(f,encoding='utf8'))
    for k,v in d['by_source'].items(): tm.setdefault(k,v)
JP=re.compile(r'[぀-ヿ一-鿿]')
tbl={}
for l in open('external/textpet-plugins/exe5ds-utf8.tbl',encoding='utf8'):
    l=l.rstrip('\r\n')
    if '=' in l:
        k,v=l.split('=',1)
        if re.fullmatch('[0-9A-F]+',k): tbl.setdefault(v,k)
print(len(tbl))
inv={v:k for k,v in tbl.items()}
print(''.join(f'{k}={v} ' for k,v in sorted(inv.items()) ))
pop=json.load(open('work/population.json',encoding='utf8'))
F=collections.Counter()
A={}
for n in pop:
    t=open(f'work/tpl/{n}.tpl',encoding='utf8').read()
    o=[];k=[]
    for sc,db,sp,s in parse(t):
        if JP.search(s):
            o.append(s);k.append(tm.get(s,s))
    A[n]=(o,k)
    for s in k:
        for c in s:
            if '가'<=c<='힣':F[c]+=1
print('음절',len(F),sum(F.values()))
top=[c for c,_ in F.most_common()]
for N in (100,150,200,228,300,400,484):
    print(N,sum(F[c] for c in top[:N])*100//sum(F.values()),end=' | ')
print()
def blen(s):  # 원문 길이
    n=0
    for c in s:
        if c=='\n':n+=1
        else: n+=len(tbl.get(c,'0000'))//2
    return n
for N in (150,200,250):
    S=set(top[:N])
    def klen(s):
        n=0
        for c in s:
            if '가'<=c<='힣':n+=1 if c in S else 2
            elif c in tbl: n+=len(tbl[c])//2
            else:n+=2
        return n
    to=tk=0;grew=[]
    for n,(o,k) in A.items():
        a=sum(map(blen,o));b=sum(map(klen,k));to+=a;tk+=b
        grew.append((b-a,n,a,b))
    grew.sort(reverse=True)
    print(N,'원문',to,'번역',tk,'%.3f'%(tk/to),grew[:10])
