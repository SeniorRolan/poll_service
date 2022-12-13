from fastapi import FastAPI, Response
from db_poll import CreatePoll, Poll
from redis_om.model import NotFoundError
from typing import Optional
from redis_om import Migrator
from loguru import logger


app = FastAPI(title="Poll-service")


def build_results(polls):
    response = []
    for elem in polls:
        response.append(elem.dict())
    if response:
        return {"results": response}
    else:
        return 0


@app.post(
    "/poll",
    description="Создание опроса"
)
async def create_poll(create: CreatePoll, response: Response):
    try:
        poll = Poll(name=create.name, description=create.description)
        logger.debug(f"Got name and description: {poll}")
        poll.save()
        response.status_code = 201
        return f'/poll/{poll.pk}'
    except Exception as e:
        response.status_code = 500
        logger.error(f'Response code: {response.status_cod}, error: {e}')
        return 'Server error'


@app.put(
    "/poll/{id}",
    description="Редактирование опроса"
)
async def edit_poll(id: str, new_poll: CreatePoll, response: Response):
    try:
        poll = Poll.get(pk=id)
        logger.debug(f'Got poll: {poll} with id: {id}')
        if poll.is_active == 1 and poll.is_deleted == 0:
            logger.info('Poll is active and not deleted')
            poll.name, poll.description = new_poll.name, new_poll.description
            logger.debug(f'Update name and description. Active: {poll.name}, Description: {poll.description}')
            poll.save()
            logger.debug(f'id = {poll.pk}')
            response.status_code = 200
            return poll.pk
        elif poll.is_active == 0:
            logger.error(f'Poll is not active')
            response.status_code = 400
            return "Poll is not active"
        else:
            logger.error('Poll is deleted')
            response.status_code = 400
            return "Poll is deleted"
    except NotFoundError:
        logger.error('Poll is not found')
        response.status_code = 404
        return 404, "Not Found id"


@app.delete("/poll/{id}", description="Удаление опроса")
async def delete_poll(id: str, response: Response):
    try:
        poll = Poll.get(pk=id)
        logger.debug(f'Got Poll with id: {id}')
        poll.is_active = 0
        poll.is_deleted = 1
        poll.save()
        logger.info('Poll successfully deleted!')
        response.status_code = 200
        return 'ok'
    except NotFoundError:
        logger.error('Poll not found!')
        response.status_code = 404
        return "Not Found id"


@app.patch(
    "/poll/{id}",
    description="Изменение статуса опроса"
)
async def activate_poll(id: str, response: Response):
    try:
        poll = Poll.get(pk=id)
        logger.debug(f'Got Poll with id: {id}')
        poll.is_active = abs(poll.is_active - 1)
        poll.save()
        logger.debug(f'Poll activate status changed from: {abs(poll.is_active - 1)} to: {poll.is_active}')
        response.status_code = 200
        return poll.pk
    except NotFoundError:
        logger.error('Poll is not found!')
        response.status_code = 404
        return "Not Found id"


# TODO удалить нахер
@app.get(
    "/poll/get_all"
)
async def get_all():
    return Poll.all_pks()


@app.get(
    "/poll/{id}", description="Получить опрос по id"
)
async def get_poll(id: str, response: Response):
    try:
        poll = Poll.get(pk=id)
        logger.debug(f'Got Poll with id: {id}')
        if poll.is_active == 1 and poll.is_deleted == 0:
            logger.info('Poll is active and not deleted')
            logger.debug(f'poll = {poll.dict()}')
            response.status_code = 200
            return poll.dict()
        elif poll.is_active == 0:
            logger.error('Poll is not active!')
            response.status_code = 400
            return "Poll is not active"
        else:
            logger.error("Poll is deleted!")
            response.status_code = 400
            return "Poll is deleted"
    except NotFoundError:
        logger.error(f'Not found id: {id}')
        response.status_code = 404
        return "Not Found id"


@app.get(
    "/poll",
    description="Получить список опросов с фильтрацией"
)
async def get_poll_list(response: Response, sort: Optional[str] = None,
                        name: Optional[str] = None, desc: Optional[str] = None):
    try:
        Migrator().run()
        poll = Poll.find(
            (Poll.name == name) &
            (Poll.description == desc)
        ).sort_by(sort).all()
        logger.debug(f'Filter poll by name: {name}, description: {desc}')
        logger.debug('Successfully found!')
        if build_results(poll):
            response.status_code = 200
            return build_results(poll)
        else:
            response.status_code = 404
            return 'Polls not found'
    except NotFoundError:
        logger.error('Polls not found')
        response.status_code = 404
        return 'Not Found'


logger.add('debug.log', format="{time} {level} {message}", level="DEBUG", rotation="10 MB", compression="zip")
