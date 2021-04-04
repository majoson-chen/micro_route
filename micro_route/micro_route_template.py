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
micro_route 的模板渲染模块.
"""
import micropython
from micropython import const




class Template_Render (object):
    _tags = ("if", "elif", "else", "for")
    _data:str
    _global:dict
    _local:dict
    
    def __init__ (self, 
        sct_prefix:str  = "{%",
        sct_suffix:str  = "%}",  # 结构控制后缀
        var_prefix:str  = "{[", # 获取变量前缀
        var_suffix:str  = "]}", # 获取变量后缀
    ):
        self._sct_prefix = sct_prefix   # 结构控制前缀
        self._sct_suffix = sct_suffix   # 结构控制后缀
        self._sct_fix_len = len (self._sct_prefix)
        self._var_prefix  = var_prefix # 获取变量前缀
        self._var_suffix  = var_suffix # 获取变量后缀
        self._var_fix_len = len (self._var_prefix)

    
    def rende (self) -> str:
        """
        :return: str
        rende the template.
        """
        result = ""
        length = len (self._data)
        cursor = 0 # 游标

        def next_ (n=1) -> str:
            """
            :param n: 欲获取的字符数量
            获取下一个字符
            """
            nonlocal cursor
            char = self._data[cursor:cursor+n]
            cursor += n
            return char
            
        def tag_handler ():
            nonlocal result
            char = next_ () # 获取一个字符
            
            
        while cursor < length:
            char = next_ ()
            if char == self._sct_prefix[0]: # 匹配到结构语法前缀
                prefix = char + next_ ( self._sct_fix_len - 1 )
                if prefix == self._sct_prefix:
                    # 匹配到结构前缀
                    ...
            elif char == self._var_prefix[0]: # 匹配到变量语法前缀
                prefix = char + next_ ( self._var_fix_len - 1 )
                if prefix == self._var_prefix:
                    # 匹配到变量结构前缀.
                    ...
            else:
                result += char # 没有特殊语义,直接添加到结果中