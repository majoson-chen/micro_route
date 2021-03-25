import network, gc, time, micropython, ujson

WLAN = network.WLAN (network.STA_IF)
WLAN.active (True)
WLAN.connect ("YMJK","YM87C37H87E13N")
gc.collect ()

import micro_route
micro_route.DEBUG = 4 # set Debug level
app = micro_route.MICRO_ROUTE ()

@app.route ("/")
def index (context:micro_route.Context):
    context.response.redirect ("/index.html")


micro_route.debug_info (1,'run app')
app.run (blocked=True)
micro_route.debug_info (1,'app ran out.')
app.stop ()
