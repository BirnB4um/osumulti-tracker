FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    cron \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

ENV TZ=Europe/Berlin

WORKDIR /opt/osu_multi
COPY requirements.txt .

RUN python -m pip install --upgrade pip \
&& python -m pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /opt/osu_multi/data/token

COPY src /opt/osu_multi/src
# COPY .env /opt/osu_multi/.env
COPY start.sh .
RUN chmod 755 start.sh

# COPY cron /etc/cron.d/osu_multi

ENTRYPOINT ["./start.sh"]
