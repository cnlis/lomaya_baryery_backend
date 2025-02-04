import datetime
import json
import random
from datetime import timedelta

import factory
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import scoped_session, sessionmaker

from src.core.db import models
from src.core.db.models import Report, Shift, Task
from src.core.services.shift_service import FINAL_MESSAGE
from src.core.settings import settings

MAX_USER_BIRTH_DATE = datetime.date(1986, 1, 1)
MIN_USER_BIRTH_DATE = datetime.date(2016, 1, 1)

engine = create_engine(settings.database_url.replace("+asyncpg", "+psycopg2"))
session = scoped_session(sessionmaker(bind=engine))


class BaseFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        sqlalchemy_session = session
        sqlalchemy_session_persistence = "commit"


class UserFactory(BaseFactory):
    class Meta:
        model = models.User

    id = factory.Faker("uuid4")
    name = factory.Faker("first_name")
    surname = factory.Faker("last_name")
    date_of_birth = factory.Faker("date_between_dates", date_start=MAX_USER_BIRTH_DATE, date_end=MIN_USER_BIRTH_DATE)
    city = factory.Iterator(["Москва", "Санкт-Петербург", "Казань", "Нижний Новгород", "Екатеринбург", "Хабаровск"])
    phone_number = factory.Sequence(lambda n: str(89991234567 + n))
    telegram_id = factory.Sequence(lambda n: 123556787 + n)
    status = factory.Iterator([status for status in models.User.Status])
    telegram_blocked = False


class ShiftFactory(BaseFactory):
    class Meta:
        model = models.Shift

    id = factory.Faker("uuid4")
    status = factory.Iterator([status for status in models.Shift.Status])
    title = factory.Faker("text", max_nb_chars=25)
    final_message = FINAL_MESSAGE
    sequence_number = factory.Sequence(int)

    @factory.lazy_attribute
    def started_at(self):
        if self.status == Shift.Status.STARTED:
            # устанавливается дата старта активной смены с учетом временной дельты от текущего дня
            return datetime.date.today() - timedelta(days=30)
        if self.status == Shift.Status.PREPARING:
            last_started_shift = session.execute(select(Shift).order_by(Shift.finished_at))
            last_started_shift = last_started_shift.scalars().first()
            return last_started_shift.finished_at + timedelta(days=random.randrange(4, 7))
        if self.status == Shift.Status.FINISHED:  # noqa R503
            # из всех существующих смен берется самая ранняя смена, дата старта которой является точкой
            # отсчета для формирования даты старта создаваемой смены (учитывается рандомный интервал между сменами и
            # продолжительность смены 90 дней)
            last_started_shift = session.execute(select(Shift).order_by(Shift.started_at))
            last_started_shift = last_started_shift.scalars().first()
            return last_started_shift.started_at - timedelta(days=random.randrange(4, 7)) - timedelta(days=90)

    @factory.lazy_attribute
    def finished_at(self):
        return self.started_at + timedelta(days=90)

    @classmethod
    def _setup_next_sequence(cls):
        starting_seq_num = 1
        return starting_seq_num  # noqa: R504

    @factory.lazy_attribute
    def tasks(self):
        task_ids = session.execute(select(Task.id).order_by(func.random()))
        task_ids = task_ids.scalars().all()
        task = {}
        count = 1
        for task_id in task_ids:
            uuid_str = str(task_id)
            task[count] = uuid_str
            count += 1
        return json.dumps(task)


class RequestFactory(BaseFactory):
    class Meta:
        model = models.Request

    id = factory.Faker("uuid4")
    status = factory.Iterator([status for status in models.Request.Status])


class ReportFactory(BaseFactory):
    class Meta:
        model = models.Report

    report_url = factory.Sequence(lambda n: f"photos/some_photo_{n}.png")

    @factory.lazy_attribute
    def status(self):
        if self.task_date < datetime.date.today():
            return random.choice([Report.Status.APPROVED, Report.Status.DECLINED])
        return Report.Status.REVIEWING

    @factory.lazy_attribute
    def task_id(self):
        task_ids = session.execute(select(Task.id).order_by(func.random()))
        return task_ids.scalars().first()


class MemberFactory(BaseFactory):
    class Meta:
        model = models.Member

    id = factory.Faker("uuid4")
    status = factory.Iterator([status for status in models.Member.Status])
    numbers_lombaryers = factory.Faker("random_int", min=0, max=92)

    @factory.post_generation
    def add_several_reports(self, created, count, **kwargs):
        start_date = session.execute(select(Shift.started_at).where(Shift.id == self.shift_id))
        start_date = start_date.scalars().first()
        all_dates = list((start_date + timedelta(day)) for day in range(91))
        for date in all_dates:
            if date <= datetime.date.today():

                if created and count:
                    ReportFactory.create_batch(
                        count,
                        member_id=self.id,
                        shift_id=self.shift_id,
                        task_date=date,
                        uploaded_at=datetime.datetime.combine(
                            date, datetime.time(hour=random.randrange(0, 24), minute=random.randrange(0, 60))
                        ),
                    )

    @classmethod
    def complex_create(cls, count, **kwargs):
        return cls.create_batch(
            count,
            add_several_reports=1,
            **kwargs,
        )
