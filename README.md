BowerPkg
========

BowerPkg accelerates the installation of Bower components
(in your Dockerfile).

* Client sends `bower.json` to server.
* Server starts a Bower container to run `bower install`.
* Server compresses the `bower_components` directory and sends
  the archive file back to the client.
* Client sends the same `bower.json`, download the cached
  archive file directly.

In your Dockerfile:

```Dockerfile
RUN curl <ADDR>/pkg \
    -H 'Content-Type: application/json' \
    --data-binary @/your-project/bower.json \
    -Ls | tar xfvz -
```
