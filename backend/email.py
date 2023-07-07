import random
import smtplib

from backend.constants import Constants

from motor.motor_asyncio import AsyncIOMotorClient

constants = Constants()
verification_collection = AsyncIOMotorClient(constants.MONGO_URL)["blog"]["verification"]

async def send_verification_email(email: str) -> None:
    verification_code: int = random.randint(100000, 999999)
    await verification_collection.insert_one(
        {
            "email": email,
            
        }
    )

    smtp = smtplib.SMTP(
        host = constants.SMTP_HOST,
        port = constants.SMTP_PORT
    )
    smtp.starttls()
    smtp.login(
        constants.SMTP_EMAIL,
        constants.SMTP_PASSWORD
    )

    smtp.sendmail(
        constants.SMTP_EMAIL,
        email,
        f"Subject: Verify your email\n\nYour verification code is {verification_code}."
    )