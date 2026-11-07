import glob,sys,json
ram=open(sys.argv[1],'rb').read()
pop=json.load(open('work/population.json',encoding='utf8'))
for n,v in pop.items():
    d=open(f'work/msg/{n}.msg','rb').read()
    if len(d)<40:continue
    i=ram.find(d[:min(len(d),64)])
    while i>=0:
        print(n,hex(0x02000000+i),len(d),'full' if ram[i:i+len(d)]==d else 'part');i=ram.find(d[:64],i+1)
