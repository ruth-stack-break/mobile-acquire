from src.device import AndroidDevice

phone = AndroidDevice()

phone.connect()

info = phone.get_metadata()

print(info)