
# For more information about this base image, see
# https://hub.docker.com/r/lambci/lambda
#FROM lambci/lambda:python3.7  # does not yet build OK due to permissions

FROM python:3.7

WORKDIR /app
COPY requirements.txt ./
RUN echo "uvicorn" >> requirements.txt \
    && python3 -m pip install -U -r requirements.txt \
    && python3 -m pip check

COPY ./example_app ./example_app

EXPOSE 8000

CMD ["uvicorn", "example_app.main:app", "--host", "0.0.0.0", "--port", "8000"]
