FROM apache/airflow:slim-latest-python3.12

RUN airflow db migrate

RUN airflow users create \
    --username rdwatch \
    --password rdwatch \
    --firstname rdwatch \
    --lastname admin \
    --role Admin \
    --email admin@localhost
