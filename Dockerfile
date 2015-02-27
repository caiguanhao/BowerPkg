FROM python:2.7.8

MAINTAINER Cai Guanhao <caiguanhao@gmail.com>

WORKDIR /bowerpkg

ADD requirements.txt /bowerpkg/requirements.txt

RUN pip install -r requirements.txt;

EXPOSE 3000

CMD bottle.py --bind 0.0.0.0:3000 --server gevent server:app

ADD . /bowerpkg
