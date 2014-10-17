# this is copied from @natronics: https://github.com/open-notify/Open-Notify-API/blob/master/util.py

from functools import wraps
from flask import jsonify, request, current_app

def safe_float(s, range, default=False):
    try:
        f = float(s)
    except:
        return default

    if f > range[1]:
        return default
    if f < range[0]:
        return default

    return f


# json endpoint decorator
def json(func):
    """Returning a object gets JSONified"""
    @wraps(func)
    def decorated_function(*args, **kwargs):
        return jsonify(func(*args, **kwargs)[0]), func(*args, **kwargs)[1]
    return decorated_function

# from farazdagi on github
#   https://gist.github.com/1089923
def jsonp(func):
    """Wraps JSONified output for JSONP requests."""
    @wraps(func)
    def decorated_function(*args, **kwargs):
        callback = request.args.get('callback', False)
        if callback:
            data = str(func(*args, **kwargs)[0].data)
            content = str(callback) + '(' + data + ')'
            mimetype = 'application/javascript'
            return current_app.response_class(content, mimetype=mimetype), func(*args, **kwargs)[1]
        else:
            return func(*args, **kwargs)
    return decorated_function


# from aisipos on github
#   https://gist.github.com/aisipos/1094140
def support_jsonp(f):
    """Wraps JSONified output for JSONP"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        callback = request.args.get('callback', False)
        if callback:
            content = str(callback) + '(' + str(f(*args,**kwargs).data) + ')'
            return current_app.response_class(content, mimetype='application/javascript')
        else:
            return f(*args, **kwargs)
    return decorated_function

