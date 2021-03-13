# Copyright 2021 github@Li-Lian1069 m-jay.cn
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# @author m-jay
# @E-mail m-jay-1376@qq.com
"""
在MicroPython上实现的类 Flask web服务器,支持单线程,多线程,阻塞和非阻塞.

例子:
import micro_route
app = micro_route.MICRO_ROUTE()

@app.route('/')
def index (context:micro_route.Context):
    return f"Welcome {context.request.addr[0]}."

app.run()

@TODO:
    default 404 not found page
    template render
    file upload
    response.cookie
    session
    gizp supported
    cache control
    Etag
    
    @app.berfore_request ()
    @app.after_request ()
    @app.before_response ()
    @app.before_request ()
"""

try: import      socket
except: import   usocket   as socket

try: import      asyncio
except: import   uasyncio  as asyncio

try: import      re
except: import   ure       as re

try: import      time
except: import   utime     as time

try: import      json
except: import   ujson     as json

try: import      _thread
except: _thread = None

import           gc, micropython, os   

# ++++++++++++++++++++++++++++++++++++++++++++
# ===================CONSTS===================
charset = micropython.const ("utf-8")
DEBUG = micropython.const(1)
_HTML_ESCAPE_CHARS = micropython.const({
    "&amp;"   :  "&",
    "&quot;"  :  '"',
    "&apos;"  :  "'",
    "&gt;"    :  ">",
    "&lt;"    :  "<",
    "&nbsp"   :  " "
})
STATU_CODES:dict = micropython.const({
    '200' : 'OK', # 客户端请求成功
    '201' : 'Created', # 请求已经被实现，而且有一个新的资源已经依据请求的需要而创建，且其URI已经随Location头信息返回。
    '301' : 'Moved Permanently', # 被请求的资源已永久移动到新位置，并且将来任何对此资源的引用都应该使用本响应返回的若干个URI之一
    '302' : 'Found', # 在响应报文中使用首部“Location: URL”指定临时资源位置
    '304' : 'Not Modified', # 条件式请求中使用
    '403' : 'Forbidden', # 请求被服务器拒绝
    '404' : 'Not Found', # 服务器无法找到请求的URL
    '405' : 'Method Not Allowed', # 不允许使用此方法请求相应的URL
    '500' : 'Internal Server Error', # 服务器内部错误
    '502' : 'Bad Gateway', # 代理服务器从上游收到了一条伪响应
    '503' : 'Service Unavailable', # 服务器此时无法提供服务，但将来可能可用
    '505' : 'HTTP Version Not Supported' # 服务器不支持，或者拒绝支持在请求中使用的HTTP版本。这暗示着服务器不能或不愿使用与客户端相同的版本。响应中应当包含一个描述了为何版本不被支持以及服务器支持哪些协议的实体。
})
MIME_TYPES_MAP:dict = micropython.const({
    ".txt"   : "text/plain",
    ".htm"   : "text/html",
    ".html"  : "text/html",
    ".css"   : "text/css",
    ".csv"   : "text/csv",
    ".js"    : "application/javascript",
    ".xml"   : "application/xml",
    ".xhtml" : "application/xhtml+xml",
    ".json"  : "application/json",
    ".zip"   : "application/zip",
    ".pdf"   : "application/pdf",
    ".ts"    : "application/typescript",
    ".woff"  : "font/woff",
    ".woff2" : "font/woff2",
    ".ttf"   : "font/ttf",
    ".otf"   : "font/otf",
    ".jpg"   : "image/jpeg",
    ".jpeg"  : "image/jpeg",
    ".png"   : "image/png",
    ".gif"   : "image/gif",
    ".svg"   : "image/svg+xml",
    ".ico"   : "image/x-icon"
    # others : "application/octet-stream"
})

_TEMPLATE_HTTPRESP:str = micropython.const ("""\
{http_ver} {statu_code} {statu_explane}\r\n\
{headers}\r\n\
{content}\
""")

VERSION:str = micropython.const ('v0.0.1 aplha')

__REGXP_TYPE_STRING = micropython.const("([^\d][^/|.]*)")
__REGXP_TYPE_INT = micropython.const("(\d*)")
__REGXP_TYPE_FLOAT = micropython.const("(\d*\.?\d*)")
__REGXP_TYPE_PATH = micropython.const("(.*)")
__REGXP_AGREEMENT = micropython.const("(GET|POST|HEAD|PUT|DELETE|CONNECT|OPTIONS|TRACE|PATCH) (.*) (.*)")
__REGXP_VAR_VERI = micropython.const("<(string|int|float|custom=.*):(\w+)>") # 匹配URL的规则是否为变量
# __comper_type_string = re.compile (__REGXP_TYPE_STRING)
# __comper_type_int = re.compile (__REGXP_TYPE_INT)
# __comper_type_float = re.compile (__REGXP_TYPE_FLOAT)
# __comper_type_path = re.compile (__REGXP_TYPE_PATH)
__comper_var_veri = re.compile (__REGXP_VAR_VERI)
__comper_agreement = re.compile (__REGXP_AGREEMENT)
# ===================CONSTS===================
# --------------------------------------------

# ++++++++++++++++++++++++++++++++++++++++++++
# =============Helper functions===============
def debug_info (level:int,*args):
    """
    如果处于调试状态,打印相应的调试信息
    @param level: 0=crash 1=error 2=warn 3=info 4=debug
    """
    if level <= DEBUG: print (*args)

def make_path (str_l:list) -> str:
    """
    把一个str的list合并在一起,并用 '/' 分割
    -> ['api','goods']
    <- "/api/goods/"
    """
    if str_l == []:
        return '/'

    s = ''

    for i in str_l:
        if i == '': 
            continue # 过滤空项
        s += "/"
        s += i

    return s

def split_url (url:str) -> list:
    """
    将字符串URL分割成一个LIST

    -> '/hello/world'
    <- ['hello', 'world']
    """
    return [ x for x in url.split ("/") if x != ""] # 去除数组首尾空字符串

def parse_url (url:str) -> str:
    """
        规范化 URL
    
    -> hello/world
    <- /hello/world/
    """
    if url == "": url = "/"
    if not url.startswith ('/'): url = "/" + url # 添加开头斜杠
    # if not url.endswith ("/"): url += "/" # 添加末尾斜杠
    return url
# =============Helper functions===============
# --------------------------------------------
class __Request ():
    """
    用来获取请求的一些信息
    """
    method:str       = "" # 请求方式,一般为 (GET|POST|HEAD|PUT|DELETE|CONNECT|OPTIONS|TRACE|PATCH)
    url:str          = "" # 请求的URL
    http_version:str = "" # 报文的HTTP协议版本
    headers:dict     = {} # HTTP报文的 Headers
    args:tuple       # URL中的参数
    addr:tuple       # 请求的TCP地址 (ip,port)
    form:dict        = {} # method = post 时可用
    args:dict        = {}
    data:bytes       = b""
    def __init__ (self,sock:socket.socket,addr:tuple,head:str,headers:str,content:str=None):
        #head => ('GET','/',"HTTP/1.1")
        self.method ,  self.url , self.http_version = head
        self.addr = addr
        self.headers = headers
        self.client = sock

        if "?" in self.url:
            # 解析参数
            self.args = self.dump_form_data (self.url[self.url.find ("?")+1:])
            
    def recv_data (self,bufsize:int=4096) -> bytes:
        """
        当请求为POST或者PUT时,服务器可能会接受到较大的数据.
        这些数据的大小可能会超出芯片内存的限制, 所以程序默认不读取请求的数据.
        可以调用本对象的 dump_data() 把表单或者 json 数据转换为 python 数据并返回.
        """
        return self.client.recv (bufsize)
    
    @staticmethod
    def escape_chars (string:str) -> str:
        """
        将转化过的html还原
        @param string: 可以是一个 str, 也可以是一个 list[str]
        @return 输入 str 类型返回 str 类型 , 输入 list 类型返回 list 
        例如:
        escape_chars ("hello&nbspworld") -> "hello world"
        """

        if type (string) == str:
            for k, v in _HTML_ESCAPE_CHARS.items ():
                string = string.replace (k,v)
        elif type (string) == list:
            for k, v in _HTML_ESCAPE_CHARS.items ():
                for idx in range(len(string)):
                    string [idx] = string [idx].replace (k,v)
        return string

    def dump_form_data (self,data:str):
        """
        传入一个bytes或者str,将其解析成Python的dict对象,用于解析HTML的表单数据
        例如:
        dump_form_data ("user_name=abc&user_passwd=123456")
        -> {
            "user_name"   : "abc",
            "user_passwd" : "123456"
        }
        """
        if type (data) == bytes:
            data = data.decode (charset)

        obj = {}
        data:list = data.split ("&")

        if not data == ['']: # data 有数据时再进行解析
            data = self.escape_chars (data)
            for line in data:
                idx = line.find ("=")
                # arg_name  : line [:idx]
                # arg_value : line [idx+1:]
                obj [line [:idx]] = line [idx+1:]
        return obj

class __SESSION ():
    """
    利用COOKIE实现的SESSION对话
    """
    # TODO
    def __init__ (self):
        pass

class __Response ():
    """
    用于回应浏览器发起的请求, 可以在处理函数中使用 return 返回内容, 程序将自动处理
    如果您使用了 send () 或者 close () , 处理函数的返回值会自动被忽略.
    """
    headers:dict = {
        "Server" : "micro_route {0}".format (VERSION),
    }

    _responsed:bool = False # 是否已经回应过
    _closed:bool = False
    __header_sended = False

    client:socket.socket
    mime_type:str = "text/html" # 默认mime类型
    statu_code:str = "200" # 默认状态


    def __init__ (self,sock:socket.socket):
        self.client = sock

    def __dump_headers (self) -> str:
        """
        将一个dict类型的header变为str
        """
        s = ""
        for k, v in self.headers.items ():
            s += k + ": " + str(v) + "\r\n"
        return s

    def send_header (self,
        statu_code:str = "200",
        statu_explane:str = None,
        content:str = ""
    ):
        """
        发送响应的头部内容(包括状态码), 然后你可以使用 send () 自定义发送你想要的数据.
        可以传入一个dict,将会在默认 headers 的基础上添加作为 headers 的内容.
        例如:
            send_header ({
                "Content-Type" : "text/plain"
            })
        """
        self.statu_code = statu_code
        if statu_explane: self.statu_explane = statu_explane
        else: self.statu_explane = STATU_CODES.get (self.statu_code,"")
        
        self.headers["Content-Type"] = self.mime_type
        self.headers["Connection"] = "close"

        try:
            self.client.send (_TEMPLATE_HTTPRESP.format (
                http_ver="HTTP/1.1",
                statu_code=self.statu_code,
                statu_explane=self.statu_explane,
                headers = self.__dump_headers (),
                content= content
            ).encode (charset))
            self.__header_sended = True
            debug_info (3,"header sended.")
        except:
            raise TimeoutError ("Faild to send headers.")

    def send (self,content:str):
        """
        向客户发送数据,建议数据不宜过大,可能造成发送不完整
        如果需要发送大量数据可以使用流式多次调用send()发送
        如果您在相应期间调用过 send () , 那么您的处理函数返回的数据将会被忽略.
        """
        if not self.__header_sended:
            self.send_header ()

        try:
            if type (content) == bytes:
                self.client.send (content)
            else:
                self.client.send (content.encode (charset))
            self._responsed = True
        except:
            raise TimeoutError ("Can not send data.")

    def redirect (self,location:str,statu_code:str="302"):
        """
        将请求重定向到另一个地址
        @param location   : 欲重定向的地址.
        @param statu_code : http 状态码 , 302:临时定向 301:永久定向
        例子: response.redirect ('https://www.baidu.com/') 重定向至百度
        """

        self.headers ["Location"] = location
        self.send_header (statu_code)
        self._responsed = True
        self.close ()

    def close (self):
        """
        关闭客户发起的请求,此函数将会关闭
        """
        if not self._closed:
            self.client.close ()
            self._responsed = True
            self._closed = True

    def abort (self,statu_code:str=500,content:str="",statu_explane=None):
        """
        中断请求, 发送一个 statu code 后关闭连接
        """
        if content: self.headers["Content-Length"] = len (content)
        self.send_header (statu_code=statu_code,statu_explane=statu_explane,content=content)
        self._responsed = True
        self.close ()

    def send_file (self,path:str) -> bool:
        """
        传入url,发送本地的静态文件
        @param path: 文件位于Flash中的绝对路径
        成功返回True
        失败返回False
        """
        try:
            #没报错就是找到文件了
            # if url == "" or url == "/":
            #     return False

            file_size = os.stat (path)[6]
            debug_info (4, "found static file.")
            suffix = path[path.rfind ('.'):]
            # 设定文档类型
            self.mime_type = MIME_TYPES_MAP.get (suffix.lower (),"application/octet-stream")
            self.headers.update(
                {"Content-Length": str(file_size)}
            ) # 将文件大小设置进 header

            self.send_header ()
            # 分片传输文件, 一片 1k
            with open (path, 'rb') as file:
                try :
                    buf = bytearray(1024)
                    while file_size > 0 :
                        x = file.readinto(buf,1024)
                        if x < len(buf):
                            buf = memoryview(buf)[:x]
                        if not self.client.write (buf):
                            return False
                        file_size -= x
                    return True
                except :
                    return False
        except: # 报错说明没找到
            debug_info (4, "not found static file.")
            self.abort (404)
            return False

class Context ():
    request:__Request
    session:__SESSION
    response:__Response
    def __init__ (self,request:__Request, response:__Response, session:__SESSION = None):
        self.request = request
        self.response = response
        self.session = session

class MICRO_ROUTE ():
    bind_ip:str
    bind_port:int
    root_path:str
    __SOCK:socket.socket
    __routes:list = []
    # __routes = [
    #     {
    #         "rule"      : '/api/goods/([^\d][^/|.]*)/(\d*)/'
    #         "func"      : function ()
    #         "method"    : "GET"
    #         "url_vars"  : [
    #               ('goods_name', ), # str,缺省,减少转换步骤
    #               ('gid', int)
    #         ]
    #     },
    #     ...
    # ]

    def __init__ (self,
        bind_ip:str     = "0.0.0.0",
        bind_port:int   = 80,
        root_path:str   = '/www',
        sock_family:int = socket.AF_INET
    ):
        """
        实例化一个micro_route, 然后开始你的嵌入式编程之旅.
        @param bind_ip   : 绑定的IP,默认为 "0.0.0.0",
        @param bind_port : 绑定的端口,默认为 80
        @param root_path : 静态文件的存放路径,默认为 '/www'
        """
        self.bind_ip = bind_ip
        self.bind_port = bind_port
        self.sock_family = sock_family

        # 清除结尾的 /
        if root_path.endswith ("/"): root_path = root_path [:-1]
        self.root_path = root_path.replace ('../', '/')
        
    def append_to_route_tree (self,rule:str,func:object,method:str,var_l:list,auto_recv:bool):
        """
        添加到路由解析树中
        """
        # @app.route ("/api/goods/<string:goods_name>/<int:gid>/")
        # def api (goods_name:str,gid:int):
        #     ...
        #                      
        # __routes = [
        #     {
        #         "rule"      : "/api/goods/([^\d][^/|.]*)/"(\d*)"/"
        #         "func"      : function ()
        #         "method"    : "GET"
        #         "URL_VARS"  : ['goods_name','gid']
        #     },
        #     ...
        # ]
        debug_info (4,"append a route: " , 
            {
                "rule"      : rule,
                "func"      : func,
                "method"    : method,
                "url_vars"  : var_l,
                "auto_recv" : auto_recv
            }
        )
        self.__routes.append ({
            "rule"      : rule,
            "func"      : func,
            "method"    : method,
            "url_vars"  : var_l,
            "auto_recv" : auto_recv
        })

    def route (self,rule:str='/',method:str="GET",auto_recv:bool=True):
        """
        @param rule      : 响应的URL,支持变量方式定义,必须以 `/` 开头
        @param method    : 响应的方式 GET | POST ...
        @param auto_recv : 仅在 method 为 POST 或者 PUT 时可用\
            由于传输的数据可能过大,可以控制程序是否自动解析客户端发送的数据
            若为 False, 可以使用 context.request.recv_data () 
            手动获取用户发送的数据.

        添加一个分发路由到服务器中.
        当添加多个规则同时匹配到一个URL时,只会相应最先添加的那个函数
        定义URL变量:
        使用 <type:var_name> 方式定义
        例如:
            @app.route ("/api/<string:api_name>/<int:numbers>")
            def api (context:micro_web.Context, api_name:str, numbers:int,**kwargs):
                ...
        使用这种方式定义之后,当WEB服务器获得相应的请求时,会将参数传递到您的响应函数中.
        请确保您的参数名填写正确
        
        目前支持的 type:
            string : 接受任何不包含斜杠的文本(缺省值) 例如: apple11 pair miui12.5
            int    : 接受正整数 例如: 20 30 21
            float  : 接受正浮点数,包括整数 例如: 12.5 20
            path   : 包含 string int float 使用path变量后面的所有变量会作废,例如 /<path:p>/<int:n>/ , 此时 n 作废
            custom : 自定义ure解析式,例如: @app.route ("/api/<custom="(.*)":var>/") 请谨慎使用此类型,可能会造成服务器的崩溃
            

        Example:
        @app.route ('/')
        def index ():
            return 'hello world'
        """
        
        def decorater (func):
            
            # ++++++++++++++++++++++++++++++++++++
            # ==============解析url===============
            l_rule = split_url(parse_url (rule))  
            url_vars:list = [] # 存放变量名称

            for i in l_rule: # 对其进行解析
                m = __comper_var_veri.match (i)
                # m.group (1) -> string | float ...
                # m.group (2) -> var_name
                if m:
                    # 如果匹配到了,说明这是一个变量参数
                    var_type = m.group (1)
                    if var_type == "string": 
                        # l_rule.index (i) 获取 i 在 l_rule 中的下标
                        l_rule[l_rule.index (i)] = __REGXP_TYPE_STRING
                        url_vars.append ((m.group (2),))
                    elif var_type == "float":
                        l_rule[l_rule.index (i)] = __REGXP_TYPE_FLOAT
                        url_vars.append ((m.group (2),float))
                    elif var_type == "int":
                        l_rule[l_rule.index (i)] = __REGXP_TYPE_INT
                        url_vars.append ((m.group (2),int))
                    elif var_type == "path":
                        l_rule[l_rule.index (i)] = __REGXP_TYPE_PATH
                        url_vars.append ((m.group (2),))
                    elif var_type.startswith("custom="):
                        l_rule[l_rule.index (i)] = m.group (1)[7:]
                        url_vars.append ((m.group (2),))
                    else:
                        raise TypeError ("Cannot resolving this variable: {0}".format (i))
                    
            
            # ==============解析url===============
            # ------------------------------------
            # 添加到路由
            # "^" + make_path(l_rule) + "/?\??" : 强制匹配开头结尾
            self.append_to_route_tree ("^" + make_path(l_rule) + "/?\??",func,method,url_vars,auto_recv)
            
            gc.collect ()
            return func
        return decorater

    def __match_rule (self,url:str,method:str) -> (callable,dict):
        """
        检索 _routes 查找是否有相应的规则被匹配
        如果被匹配,将会返回一个元组 (func,{var_name : value},auto_recv)
        如果没有被匹配,返回None
        """
        result  = None
        kw_args = {}
        for i in self.__routes:
            result = re.match (i ['rule'],url)
            if result:
                # 有结果代表匹配到了

                if not i["method"].lower () == method.lower ():
                    # 访问方式不匹配,跳过
                    continue

                # 检测是否有变量列表
                if i.get ("url_vars"): 
                    try:
                        # 获取 result 中的所的组
                        idx = 1
                        while True:
                            var_tp = i ["url_vars"][idx-1] 
                            # var_tp = (var_name, var_type)
                            # var_name = var_tp[0]

                            # 有类型则进行转化,无类型则跳过
                            if len (var_tp) == 2: # 有类型
                                # 有类型则转化
                                value = var_tp[1](result.group (idx))
                            else:
                                # 无类型说明默认为str
                                value = result.group (idx)
                            
                            # var_tp[0] 变量名
                            kw_args [var_tp[0]] = value
                            # 按顺序取出变量,放入kw_args中
                            idx += 1
                    except:
                        # 报错说明没了
                        pass
                return (i["func"],kw_args,i["auto_recv"])
        # 没有被截胡说明没有被匹配到
        return None

    def __accept_handler (self,sock:socket.socket):
        """
        接受请求的函数
        """
        if not self.__blocked and not self.__muti_thread:
            # 单线程 - 不阻塞
            # 在连接后回调执行
            try:
                client, addr = sock.accept ()
                self.__process_handler (client, addr)
            except Exception as e:
                debug_info (4,"Accept request faild: ", e)

        if self.__blocked and not self.__muti_thread:
            # 单线程 - 阻塞
            while True:
                try:
                    client, addr = sock.accept ()
                    self.__process_handler (client, addr)
                except Exception as e:
                    debug_info (4,"Accept request faild: ", e)


        if self.__muti_thread and not self.__blocked:
            # 多线程 - 不阻塞
            # 被回调调用
            try:
                client, addr = sock.accept ()
                _thread.start_new_thread (self.__process_handler,(client,addr))
                debug_info (3,"====Accepted a new request :", addr, " ====")
            except Exception as e:
                debug_info (4,"Accept request faild: ", e)


        if self.__muti_thread and self.__blocked:
            # 多线程 - 阻塞
            while True:
                try:
                    client, addr = sock.accept ()
                    _thread.start_new_thread (self.__process_handler,(client,addr))
                    debug_info (3,"====Accepted a new request :", addr, " ====")
                except Exception as e:
                    debug_info (4,"Accept request faild: ", e)
        

    def __process_handler (self,client:socket.socket,addr:tuple):
        """
        处理请求的函数
        """
        try:
            # 解析headers
            line = client.readline ().decode ().strip()
            # 读请求地址
            m = __comper_agreement.search (line)
            head = [m.group (i) for i in range(1,4)]

            headers = {}
            # Headers 解析
            while line:
                line = client.readline ().decode ().strip()
                if line != "":
                    #非空就是headers
                    idx = line.find (':')
                    headers [line[:idx]] = line [idx+2:]
                else:
                    # 空行代表报文结束
                    break
            debug_info (4,"parse headers: ", headers)
        except Exception as e:
            debug_info (3,"faild to recv headers: ", e)
            return

        # 创建 context
        context = Context (
            __Request  (client,addr,head,headers),
            __Response (client)
        )
        debug_info (3,"Context create: ", context)
        debug_info (3,"New request: ", context.request.url)

        rst = None
        # 匹配规则
        f = self.__match_rule (context.request.url,context.request.method)
        if f:
            # 有处理函数
            debug_info (3,"rule hitted.")

            method = context.request.method.lower()
            if f[2] and method == 'post' or method == 'put': # auto_recv
                debug_info (4, "recv the data part.")
                context.request.data = context.request.recv_data ()
                # 尝试解析数据
                debug_info (4, "try to load the data to form obj.")
                if "application/x-www-form" in context.request.headers ["Content-Type"]:
                    context.request.form = context.request.dump_form_data (context.request.data.decode (charset))
                elif "application/json" in context.request.headers ["Content-Type"]:
                    context.request.form = json.loads (context.request.data.decode (charset))
            del (method)

            try:
                rst = f[0](context,**f[1])
            except Exception as e:
                # 用户处理函数发生错误, 抛出 500 错误码
                context.response.abort (500)
                rts = None # 跳过发送用户数据
                debug_info (0, "handle func has some error: ", e)

            if not context.response._responsed and rst:
                # 如果用户还没操作过且有返回数据
                # 对其进行传输
                context.response.headers.update(
                    {"Content-Length": str(len (rst))}
                ) # 设置 header
                context.response.send (rst)
        else:
            # 没有处理函数, 尝试寻找本地文件
            debug_info (3,"rule not hit")
            if context.request.url == "" or context.request.url == "/":
                context.response.abort (404) # Not Found
                debug_info (3, "index page not found.")
            if context.response.send_file (self.root_path + context.request.url):
                debug_info (3, "send static file succeed.")
            else:
                debug_info (3, "send static file faild")
            
        
        context.response.close () # 关闭连接
        gc.collect ()
        debug_info (4,"------responsed------")

    def run (self,
        timeout:int      = None,
        backlog:int      = 5,
        blocked:bool     = False,
        muti_thread:bool = False
    ):
        """
        @param timeout: 等待超时的时间
        @param backlog: 最多同时连接的TCP数量
        @param blocked: 是否阻塞线程,设置为True之后除非发生错误或者用户手动中断,此函数将一直不返回
        @param muti_thread: 是否启用多线程
        @return: None
        启动WEB服务器.
        可以指定是否阻塞模式.
        """
        self.__SOCK = socket.socket (self.sock_family, socket.SOCK_STREAM)
        self.__SOCK.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # 设置快速重启 TCP
        if timeout: self.__SOCK.settimeout (timeout)  
        self.__SOCK.bind ((self.bind_ip,self.bind_port))
        self.__SOCK.listen (backlog)

        self.__muti_thread = muti_thread
        self.__blocked = blocked

        if muti_thread and not _thread:
            raise Exception ("This board may be not support to muti-thread.")

        if blocked:
            try:
                # 开始 loop
                gc.collect ()
                self.__accept_handler (self.__SOCK)
            except Exception as e:
                debug_info (0 , "listen faild: ", e, " the server will stop.")
                gc.collect ()
                self.stop ()
        else:
            self.__SOCK.setsockopt(socket.SOL_SOCKET, 20, self.__accept_handler) # 设置回调函数


    def stop (self) -> bool:
        """
        停止服务器的运行,成功返回True,出错返回Fasle
        """
        try:
            self.__SOCK.close()
            gc.collect()
            return True
        except:
            gc.collect()
            return False
