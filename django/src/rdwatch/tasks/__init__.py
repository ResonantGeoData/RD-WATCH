from celery import shared_task


@shared_task
def test_task(input_value: int) -> None:
    print(f'Testing an async task! {input_value}')
