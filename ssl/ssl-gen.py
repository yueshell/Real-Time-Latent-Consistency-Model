import os
import ssl

#gen ssl crt
os.system("openssl req -newkey rsa:2048 -nodes -keyout example.com.key -x509 -days 365 -out example.com.crt")

cert_file = 'example.com.crt'
key_file = 'example.com.key'

context = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)
context.load_cert_chain(certfile=cert_file, keyfile=key_file)


