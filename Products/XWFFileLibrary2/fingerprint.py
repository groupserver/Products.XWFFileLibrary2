import hashlib
import time
from gs.core import convert_int2b62 as u_convert_int2b62


def convert_int2b62(i):
    if type(i) not in (int, long):
        raise TypeError('Not an int')
    retval = u_convert_int2b62(i).encode('ascii', 'ignore')
    return retval


def fingerprint_file(file_object):
   """ Our file fingerprint consists of three parts:

         fingerprint = b62(ripe160(data)+'-'+b62(size)+'-'+b62(time)

       That is, we convert the ripe160 and size to a base62 (using printable
       ascii characters), before appending the size to the digest.

   """
   pos = file_object.tell()
   if pos != 0:
       file_object.seek(0)

   digest = hashlib.new('ripemd160')

   # iterate through in 2MB blocks
   bs = 2**21
   data = file_object.read(bs)
   while data:
       digest.update(data)
       data = file_object.read(bs)

   size = file_object.tell()

   # reset to original position
   file_object.seek(pos)

   fingerprint = convert_int2b62(long(digest.hexdigest(), 16))+'-'+convert_int2b62(size)+'-'+convert_int2b62(int(time.time()*100))

   return fingerprint

def fingerprint_data(data):
   """ Our data fingerprint consists of two parts:

         fingerprint = b62(ripe160(data)+'-'+b62(size)

       That is, we convert the ripe160 and size to a base62 (using printable
       ascii characters), before appending the size to the digest.

   """
   digest = hashlib.new('ripemd160')
   digest.update(data)
   size = len(data)

   fingerprint = convert_int2b62(long(digest.hexdigest(), 16))+'-'+convert_int2b62(size)+'-'+convert_int2b62(int(time.time()*100))

   return fingerprint
