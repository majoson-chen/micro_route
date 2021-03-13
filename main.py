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
    return """\
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Welcome</title>
    <style>
        body {
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            padding: 0;
            margin: 0
        }
        h1 {
            font-size: 32px;
        }
        p {
            font-size: 24px;
        }
    </style>
</head>
<body>
    <div>
        <h1>Welcome to micro_route</h1>
        <p>Start a pleasant development journey!</p>
    </div>
</body>
</html>
"""


micro_route.debug_info (1,'run app')
app.run (blocked=True)
micro_route.debug_info (1,'app ran out.')
app.stop ()
