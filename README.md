BowerPkg
========

BowerPkg accelerates the installation of Bower components
(in your Dockerfile).

* Client sends `bower.json` to server.
* Server starts a Bower container to run `bower install`.
* Server compresses the `bower_components` directory and sends
  the archive file back to the client.
* Cached archive file will be downloaded directly if client
  sends the same `bower.json`.

This is helpful if you are in a poor network connecting GitHub.
For example, in China, it would take up to 5 minutes to simply
download jQuery via Bower; using HTTP proxy server makes it a
little faster, but it takes the same long time every time
`docker build` runs the command; so, the fastest way would be
setting up a BowerPkg server on a Linode VPS (or any other
servers that install bower components instantly).

In your Dockerfile, replace:

```Dockerfile
WORKDIR /project
ADD bower.json /project/bower.json
RUN git config --global http.proxy http://username:password@example.com:1080; \
    echo '{"proxy":"http://username:password@example.com:1080",\
    "https-proxy":"http://username:password@example.com:1080"}' > .bowerrc
RUN bower install --production --force-latest \
                  --allow-root --config.interactive=false
```

with:

```Dockerfile
WORKDIR /project
ADD bower.json /project/bower.json
RUN curl <BowerPkg-Address>/pkg \
    -H 'Content-Type: application/json' \
    --data-binary @/project/bower.json \
    -Ls | tar xfvz -
```

USAGE
-----

Run `docker-compose up -d` to start the service.
Note: Once the service has been started,
a new image called `bower` will be built automatically.

LICENSE: MIT
