from config import database_uri
from tortoise import Tortoise


TORTOISE_ORM = {
    "connections": {"default": database_uri},
    "apps": {
        "models": {
            "models": ["models", "aerich.models"],
            "default_connection": "default",
        },
    },
}


async def db_init():
    await Tortoise.init(
        db_url=database_uri,
        modules={'models': ['models']}
    )
    # Generate the schema
    await Tortoise.generate_schemas()
