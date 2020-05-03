FROM python:3.7

## See also
## - https://github.com/lambci/docker-lambda/issues/57
## - https://github.com/myrmex-org/docker-lambda-packager
#FROM lambci/lambda:build-python3.7
##RUN rm /var/runtime/awslambda/runtime.cpython-36m-x86_64-linux-gnu.so
#COPY runtime_mock.py /var/runtime/awslambda/runtime.py

WORKDIR /app
COPY requirements.txt ./
RUN echo "uvicorn" >> requirements.txt \
    && python3 -m pip install -U -r requirements.txt \
    && python3 -m pip check

COPY ./example_app ./example_app

EXPOSE 8080

CMD ["uvicorn", "example_app.main:app", "--host", "0.0.0.0", "--port", "8080"]
