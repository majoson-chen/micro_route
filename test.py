# esptool --port COM6 erase_flash
# esptool --port COM6 --baud 460800 write_flash --flash_size=detect -fm dio 0 .\esp8266-20210202-v1.14.bin


# d = {
#     "a":123,
#     "b" : 10086,
#     "C" : 233155
# }

# s = ""
# for k, v in d.items ():
#     s += k + ": " + str(v) + "\r\n"
# print (s.encode ('utf-8'))

for i in range (5):
    if i == 2:
        raise Exception ("aaa")
    print (i)
