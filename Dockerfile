FROM python:2.7.8

MAINTAINER Cai Guanhao <caiguanhao@gmail.com>

WORKDIR /bowerpkg

ADD requirements.txt /bowerpkg/requirements.txt

RUN pip install -r requirements.txt;

EXPOSE 3000

CMD python server.py

ADD . /bowerpkg
