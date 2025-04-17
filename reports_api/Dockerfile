FROM python:3.11.0
MAINTAINER Komal Thareja<komal.thareja@gmail.com>

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app
VOLUME ["/usr/src/app"]

COPY docker-entrypoint.sh /usr/src/app/
COPY . /usr/src/app/reports_api
COPY README.md /usr/src/app/
COPY LICENSE /usr/src/app/

RUN pip3 install --no-cache-dir -r /usr/src/app/requirements.txt

EXPOSE 8080

ENTRYPOINT ["/usr/src/app/docker-entrypoint.sh"]
CMD ["reports_api"]