# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)
import uos, machine
#uos.dupterm(None, 1) # disable REPL on UART(0)
import micropython
import gc
#import webrepl
#webrepl.start()
machine.freq (160000000)
micropython.alloc_emergency_exception_buf (100)
gc.threshold (4096)
gc.collect()