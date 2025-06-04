FROM python:3.11.0
MAINTAINER Komal Thareja<komal.thareja@gmail.com>

# Install cron
RUN apt-get update && apt-get install -y cron && rm -rf /var/lib/apt/lists/*

# Create app directory
RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app
VOLUME ["/usr/src/app"]

# Copy files
COPY docker-entrypoint.sh /usr/src/app/
COPY . /usr/src/app/reports_api
COPY README.md /usr/src/app/
COPY LICENSE /usr/src/app/

# Install dependencies
RUN pip3 install --no-cache-dir -r /usr/src/app/reports_api/requirements.txt

# Copy and install cron job
COPY cronjob /etc/cron.d/reports_sync_cron
RUN chmod 0644 /etc/cron.d/reports_sync_cron && \
    crontab /etc/cron.d/reports_sync_cron && \
    touch /var/log/cron.log \

# Expose default port
EXPOSE 8080

# Entry point and default command
ENTRYPOINT ["/usr/src/app/docker-entrypoint.sh"]
CMD ["reports_api"]