"""전 파일을 훑어 메시지 아카이브(u16 오프셋표) 후보를 찾는다. LZ10 은 풀어서 본다."""
import sys,struct,collections,pathlib,json
root=pathlib.Path('work/jp/fs')
def lz10(d):
    if len(d)<4 or d[0]!=0x10: return None
    n=int.from_bytes(d[1:4],'little')
    if n==0 or n>0x100000: return None
    o=bytearray();p=4
    try:
        while len(o)<n:
            f=d[p];p+=1
            for i in range(8):
                if len(o)>=n:break
                if f&0x80:
                    a,b=d[p],d[p+1];p+=2
                    l=(a>>4)+3;dd=((a&15)<<8|b)+1
                    if dd>len(o):return None
                    for _ in range(l):o.append(o[-dd])
                else:
                    o.append(d[p]);p+=1
                f=(f<<1)&0xff
    except IndexError:return None
    return bytes(o)
def ismsg(d):
    if len(d)<6:return False
    t=struct.unpack_from('<H',d)[0]
    if t==0 or t%2 or t>len(d):return False
    v=struct.unpack_from('<%dH'%(t//2),d)
    if any(v[i]>v[i+1] for i in range(len(v)-1)):return False
    if v[-1]>len(d):return False
    return True
def main():
    res=[]
    for f in sorted(root.rglob('*')):
        if not f.is_file():continue
        d=f.read_bytes();r=f.relative_to(root).as_posix()
        if ismsg(d): res.append((r,'raw',len(d),struct.unpack_from('<H',d)[0]//2))
        x=lz10(d)
        if x is not None and ismsg(x): res.append((r,'lz',len(x),struct.unpack_from('<H',x)[0]//2))
        if x is not None and len(x)>4 and ismsg(x[4:]) : res.append((r,'lz+4',len(x),struct.unpack_from('<H',x,4)[0]//2))
    json.dump(res,open('work/msg_scan.json','w'),indent=0)
    c=collections.Counter()
    s=collections.Counter()
    for r,k,l,n in res:
        pre=r.split('/')[-1];pre=pre.rsplit('.',1)
        c[(r.split('/')[2],k,pre[1])]+=1;s[(r.split('/')[2],k,pre[1])]+=l
    for k,v in sorted(c.items()):print(k,v,s[k])
    print(len(res))
if __name__=='__main__':main()
