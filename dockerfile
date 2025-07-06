FROM python:3.9-alpine
WORKDIR /app

ADD --chown=1000:1000 requirements.txt /app
ADD --chown=1000:1000 .patch /app/.patch

RUN apk add --no-cache gcc musl-dev linux-headers libffi-dev git
RUN pip install --no-cache-dir -r requirements.txt
RUN cd /usr/local/lib/python3.9/site-packages/telepot/ && git apply /app/.patch/loop.py.patch && cd /app
RUN apk del gcc musl-dev linux-headers libffi-dev git

USER 1000:1000
ENTRYPOINT [ "python", "PillPosting.py" ]
