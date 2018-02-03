FROM python:3-alpine

VOLUME [ "/etc/letsencrypt" ]

ENV DATABASE_NAME remembrancer
ENV DATABASE_HOST postgres
ENV DATABASE_USERNAME remembrancer
ENV DATABASE_PASSWORD password
ENV GUARD_WINDOW_DAYS 3
ENV SLEEP_SECONDS 60
ENV EMAIL email_for_letsencrypt

RUN apk add --update --no-cache --virtual=run-deps \
    openssl \
    ca-certificates \
    certbot \
    tzdata \
    postgresql-dev \
    gcc \
    python3-dev \
    musl-dev \
    git \
    libffi-dev

RUN mkdir -p /opt/remembrancer
WORKDIR /opt/remembrancer

COPY certbot /opt/certbot
RUN chmod +x /opt/certbot/route53.sh

COPY run_remembrancer.sh /opt/remembrancer/
RUN chmod +x /opt/remembrancer/run_remembrancer.sh

CMD /opt/remembrancer/run_remembrancer.sh

COPY app/requirements.txt /opt/remembrancer/
RUN pip install -r /opt/remembrancer/requirements.txt

COPY app /opt/remembrancer
