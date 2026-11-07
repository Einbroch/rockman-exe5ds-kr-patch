import sys,os
sys.path.insert(0,'tools')
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
import emutest
emu=emutest.Emu(sys.argv[1],sys.argv[2])
emu.run(2)
ram=bytes(emu.e.memory.unsigned[0x02000000:0x02400000])
open(sys.argv[3],'wb').write(ram)
emutest.shutdown()
