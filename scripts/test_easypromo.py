import asyncio
import os
from app.services.easypromo import register_and_get_play_link
from app.core.config import settings


async def main():
    # Ejemplo de usuario
    user = {
        "external_id": "1234",
        "first_name": "Asiesel",
        "last_name": "futbol",
        "nickname": "kgalarza",
        "email": "datadriven555@gmail.com",
        "phone": "",
        "country": "ES",
    }

    # Usa valores de settings por defecto si no se pasan
    try:
        result = await register_and_get_play_link(user)
    except Exception as e:
        print("Error al ejecutar register_and_get_play_link:", e)
        return

    print("Resultado:")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
