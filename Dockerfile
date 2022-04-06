#Deriving the latest base image
FROM python:latest

WORKDIR /home/spurrier0/project-demo/

COPY main.py ./

CMD [ "python", "./main.py"]
