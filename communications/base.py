import ujson
import uhashlib
import ubinascii
from ..config import config

class Communication:
    def __init__(self):
        config.init_var('communication_key', str, '')

    def recv(self):
        pass

    def send(self, data):
        pass

    def _get_verify_request(self, data):
        try:
            _data = ujson.loads(data)
            my_sign_string = _data['_p'] + config.communication_key
            my_sign_string = my_sign_string.encode()
            hash = uhashlib.sha1(my_sign_string)
            my_sign = ubinascii.hexlify(hash.digest())
            my_sign = my_sign.decode()[:20]
            if my_sign == _data['_s']:
                del _data['_s']
                del _data['_p']
                return _data
        except:
            pass
        return None