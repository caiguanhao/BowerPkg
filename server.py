from bottle import Bottle, run, abort, request, redirect, static_file
from json import dumps
from bowerpkg import BowerPkg

from gevent import monkey
monkey.patch_all()

class BowerPkg_Server(Bottle):
    def default_error_handler(self, res):
        return dumps({
            'error':   res.status,
            'message': res.body,
        }) + '\n'

app = BowerPkg_Server()
pkg = BowerPkg(store='/store')
pkg.build_bower_image()

@app.post('/pkg')
def process_bower_json():
    bower_json = request.json

    if not bower_json:
        return abort(406, 'Please provide a bower.json.')

    if not 'name'         in bower_json \
    or not 'dependencies' in bower_json \
    or not isinstance(bower_json['name'],         unicode) \
    or not isinstance(bower_json['dependencies'], dict): \
        return abort(406, 'A valid bower.json object contains ' +
            'at least two keys: name and dependencies.')

    bower_json_str = request._get_body_string()
    pkgpath = pkg.find_package(bower_json_str)
    if pkgpath: redirect(pkgpath)
    abort(406, 'Error processing bower.json.')

@app.get('/store/<path:path>')
def get_store(path):
    return static_file(path, root='/store')

run(app, host='0.0.0.0', port=3000, server='gevent')
