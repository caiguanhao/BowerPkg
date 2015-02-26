import os, errno
import sys
import base64
import shutil
import tarfile
import hashlib

from io import BytesIO
from docker.client import Client
from docker.utils import kwargs_from_env
from json import loads

class BowerPkg(object):
    BOWER_IMAGE_NAME = 'bower'
    BOWER_IMAGE_VER = '0.0.1'
    BOWER_IMAGE = '''FROM node:0.12.0
MAINTAINER Cai Guanhao <caiguanhao@gmail.com>
RUN python2.7 -c 'from urllib import urlopen; from json import loads; \
    print(loads(urlopen("http://ip-api.com/json").read().decode("utf-8" \
    ).strip())["countryCode"])' > /tmp/country
RUN test "$(cat /tmp/country)" = "CN" && { \
    (echo "registry = https://registry.npm.taobao.org" && \
    echo "disturl = https://npm.taobao.org/dist") \
    > ~/.npmrc; \
    } || true
RUN npm --loglevel http install -g bower
WORKDIR /bower
CMD env
'''

    def __init__(self, store='/store'):
        kwargs = kwargs_from_env()
        kwargs['tls'].assert_hostname = False
        self.client = Client(**kwargs)
        self.STORE = store

    def image_exists(self, img_name, img_ver='latest'):
        images = self.client.images()
        for image in images:
            for tag in image['RepoTags']:
                info = tag.split(':')
                name = info[0]
                version = info[1]
                if name == img_name and version == img_ver:
                    return True
        return False

    def build_image(self, img_name, img_ver='latest', dockerfile=''):
        tag = '%s:%s' % (img_name, img_ver)
        fileobj = BytesIO(dockerfile.encode('utf-8'))
        build = self.client.build(fileobj=fileobj, rm=True, tag=tag)
        for line in build:
            out = loads(line)['stream']
            sys.stdout.write(out.encode('utf-8'))

    def mkdirs(self, path):
        try:
            os.makedirs(path)
        except OSError as ex:
            if ex.errno == errno.EEXIST and os.path.isdir(path): pass
            else: raise

    def create_container(self, img_name, img_ver='latest', bower_json=''):
        image = '%s:%s' % (img_name, img_ver)
        shasum = hashlib.sha1(bower_json).hexdigest()
        b64 = base64.b64encode(bower_json)
        path = '%s/%s' % (self.STORE, shasum)
        jsonpath = '%s/%s' % (path, 'bower.json')
        pkgpath = '%s/%s' % (path, 'bowerpkg.tar.gz')
        logpath = '%s/%s' % (path, 'log')
        self.mkdirs(path)
        with open(jsonpath, 'w') as fd:
            fd.write(bower_json)

        env = {"BOWERJSON": b64}
        bower_install_opts = [
            '--production',
            '--force-latest',
            '--allow-root',
            '--config.interactive=false',
        ]
        shell = [
            'echo $BOWERJSON | base64 --decode > bower.json',
            'bower install %s' % ' '.join(bower_install_opts),
            'tar cfvz bowerpkg.tar.gz bower_components',
        ]
        container = self.client.create_container(
            image=image,
            environment=env,
            command="sh -c '%s'" % ' && '.join(shell),
        )
        cid = container.get('Id')
        self.client.start(container=cid)
        try:
            logs = self.client.logs(
                container=cid,
                stdout=True,
                stderr=True,
                stream=True,
            )
            with open(logpath, 'w') as fd:
                for line in logs:
                    uline = line.encode('utf-8')
                    sys.stdout.write(uline)
                    fd.write(uline)
            exit = self.client.wait(
                container=cid,
            )
            if exit != 0: raise exit
            res = self.client.copy(
                container=cid,
                resource='/bower/bowerpkg.tar.gz',
            )
            tar = tarfile.open(fileobj=BytesIO(res.data))
            tar.extractall(path=path)
            tar.close()
            return pkgpath
        except:
            shutil.rmtree(path)
        finally:
            self.client.remove_container(
                container=cid,
                force=True,
            )
        return None

    def package_exists(self, bower_json='', strict=False):
        shasum = hashlib.sha1(bower_json).hexdigest()
        path = '%s/%s' % (self.STORE, shasum)
        pkgpath = '%s/%s' % (path, 'bowerpkg.tar.gz')
        if os.path.isdir(path):
            if strict and not os.path.isfile(pkgpath):
                return None
            return pkgpath
        return None

    def find_package(self, bower_json=''):
        pkgpath = self.package_exists(bower_json)
        if pkgpath: return pkgpath
        pkgpath = self.create_container(
            img_name=self.BOWER_IMAGE_NAME,
            img_ver=self.BOWER_IMAGE_VER,
            bower_json=bower_json,
        )
        return pkgpath

    def build_bower_image(self, force=False):
        if not self.image_exists(
            self.BOWER_IMAGE_NAME,
            self.BOWER_IMAGE_VER,
        ) or force:
            self.build_image(
                self.BOWER_IMAGE_NAME,
                self.BOWER_IMAGE_VER,
                self.BOWER_IMAGE,
            )
