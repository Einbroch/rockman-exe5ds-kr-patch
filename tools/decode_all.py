"""후보 아카이브를 뽑아 TextPet(exe5ds)으로 해독하고 TPL→MSG 바이트 왕복을 증명한다.
출력: work/msg/<id>.msg, work/tpl/<id>.tpl, work/population.json"""
import json,pathlib,shutil,subprocess,sys,struct
sys.path.insert(0,'tools')
from scan_msg import lz10
R=pathlib.Path('.')
TP=str(R/'external/TextPet-v1.0.0/TextPet.exe');PL=str((R/'external/textpet-plugins').resolve())+chr(92)
scan=json.load(open('work/msg_scan.json'))
fsr=R/'work/jp/fs'
M=R/'work/msg';T=R/'work/tpl';O=R/'work/rt'
for d in (M,T,O):
    shutil.rmtree(d,ignore_errors=True);d.mkdir(parents=True)
items={}
for r,k,l,n in scan:
    d=(fsr/r).read_bytes()
    if k=='lz+4': d=lz10(d)[4:]
    elif k!='raw':continue
    s=r.split('/')[-2]+'_'+r.split('/')[-1].rsplit('.',1)[0]+('_'+r.rsplit('.',1)[1] if not r.endswith(('.msg','.bin')) else '')
    (M/(s+'.msg')).write_bytes(d);items[s]=dict(path=r,kind=k,size=len(d),scripts=n)
def tp(src,sf,dst,df):
    return subprocess.run([TP,'silent','load-plugins',PL,'game','exe5ds','read-text-archives',str(src)+chr(92),'-f',sf,'write-text-archives',str(dst)+chr(92),'-f',df],capture_output=True,text=True,encoding='utf-8',errors='replace')
def run(names):
    t=R/'work/t1';shutil.rmtree(t,ignore_errors=True);t.mkdir()
    for n in names: shutil.copy(M/(n+'.msg'),t)
    x=tp(t,'bin',T,'tpl')
    return x
names=sorted(items)
fails=[]
def rec(g):
    x=run(g)
    if all((T/(n+'.tpl')).exists() for n in g):return
    if len(g)==1:
        fails.append((g[0],(x.stdout or '')[-200:]));return
    m=len(g)//2;rec(g[:m]);rec(g[m:])
for i in range(0,len(names),60):rec(names[i:i+60])
print('tpl',len(list(T.glob('*.tpl'))),'fail',len(fails),fails[:5])
x=tp(T,'tpl',O,'bin');print((x.stdout or '')[-200:])
good=bad=0
for n,v in items.items():
    a=O/(n+'.msg')
    v['rt']=a.exists() and a.read_bytes()==(M/(n+'.msg')).read_bytes()
    good+=v['rt'];bad+=not v['rt']
print('왕복 일치',good,'불일치',bad)
json.dump(items,open('work/population.json','w'),ensure_ascii=False,indent=0)
print([n for n,v in items.items() if not v['rt']][:40])
