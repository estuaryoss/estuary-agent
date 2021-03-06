FROM alpine:3.11.6

RUN apk add --no-cache python3 && \
    pip3 install --upgrade pip==20.3.3 setuptools==46.2.0 --no-cache

RUN apk add --no-cache \
    bash \
    maven \
    openjdk8 \
    nodejs \
    npm

RUN apk add --no-cache \
    python3-dev \
    libffi-dev \
    openssl-dev \
    gcc \
    libc-dev \
    make

## Cleanup
RUN rm -rf /var/cache/apk/*

# Create a shared data volume
RUN mkdir /data/

## Expose some volumes
ENV SCRIPTS_DIR /scripts
ENV HTTPS_DIR $SCRIPTS_DIR/https
ENV WORKSPACE $SCRIPTS_DIR/inputs

VOLUME ["$WORKSPACE/templates"]
VOLUME ["$WORKSPACE/variables"]

ENV TEMPLATES_DIR $WORKSPACE/templates
ENV VARS_DIR $WORKSPACE/variables
ENV HTTP_AUTH_TOKEN None
ENV PORT 8080
ENV TZ UTC

COPY https/key.pem $HTTPS_DIR/
COPY https/cert.pem $HTTPS_DIR/
COPY inputs/templates/ $TEMPLATES_DIR/
COPY inputs/variables/ $VARS_DIR/
COPY ./ $SCRIPTS_DIR/

RUN chmod +x $SCRIPTS_DIR/*.py
RUN chmod +x $SCRIPTS_DIR/*.sh

WORKDIR $SCRIPTS_DIR

RUN pip3 install -r $SCRIPTS_DIR/requirements.txt
RUN pip3 install uwsgi

# for cmds in background
ADD https://estuary-agent-go.s3.eu-central-1.amazonaws.com/4.1.0/runcmd-alpine $SCRIPTS_DIR/runcmd
RUN chmod +x $SCRIPTS_DIR/runcmd

CMD ["/scripts/main.py"]
