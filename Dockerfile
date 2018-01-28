FROM python:3.6

ENV DATABASE_NAME remembrancer
ENV DATABASE_HOST postgres
ENV DATABASE_USERNAME remembrancer
ENV DATABASE_PASSWORD password
ENV GUARD_WINDOW_DAYS 3
ENV SLEEP_SECONDS 60

RUN mkdir -p /opt/remembrancer
WORKDIR /opt/remembrancer

CMD /opt/remembrancer/run_remembrancer.sh

COPY app/requirements.txt /opt/remembrancer/
RUN pip install -r /opt/remembrancer/requirements.txt

COPY run_remembrancer.sh /opt/remembrancer/

COPY app /opt/remembrancer
