from beanhub_inbox.data_types import InboxEmail
from factory import Dict
from factory import Factory
from factory import Faker
from factory import List


class InboxEmailFactory(Factory):
    id = Faker("uuid4")
    message_id = Faker("slug")
    headers = Dict(
        {
            "mock-header": Faker("slug"),
        }
    )
    subject = Faker("sentence")
    from_addresses = List([Faker("email")])
    recipients = List([Faker("email")])
    tags = List([Faker("slug")])

    class Meta:
        model = InboxEmail
