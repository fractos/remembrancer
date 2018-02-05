FROM python:3-alpine

VOLUME [ "/etc/letsencrypt" ]

ENV AWS_REGION region
ENV AWS_ACCESS_KEY_ID placeholder
ENV AWS_SECRET_ACCESS_KEY placeholder

ENV SSM_KEY_PREFIX remembrancer_
ENV KMS_KEY_ALIAS remembrancer

ENV DATABASE_TABLE remembrancer

ENV GUARD_WINDOW_DAYS 7
ENV SLEEP_SECONDS 60

ENV EMAIL email_for_letsencrypt

ENV SLACK_WEBHOOK_URL ""
ENV ACTIVITY_STREAM_URL ""

RUN apk add --update --no-cache --virtual=run-deps \
    openssl-dev \
    ca-certificates \
    certbot \
    tzdata \
    gcc \
    python3-dev \
    musl-dev \
    git \
    libffi-dev

RUN mkdir -p /opt/remembrancer
WORKDIR /opt/remembrancer

COPY certbot /opt/certbot
RUN chmod +x /opt/certbot/route53.sh

COPY *.sh /opt/remembrancer/

RUN chmod +x /opt/remembrancer/*.sh

CMD /opt/remembrancer/run_remembrancer.sh

COPY app/requirements.txt /opt/remembrancer/
RUN pip install -r /opt/remembrancer/requirements.txt

COPY app /opt/remembrancer
