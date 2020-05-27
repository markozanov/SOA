FROM python:3.8
RUN pip install asyncpg paho-mqtt requests uvicorn python-consul fastapi pydantic
COPY ./instancemanager.py /
EXPOSE 5000
ENTRYPOINT [ "python", "instancemanager.py" ]
