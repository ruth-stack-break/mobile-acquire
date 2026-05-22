from src.device import AndroidDevice

phone = AndroidDevice()

phone.connect()

cmd = "ls -lR /storage/emulated/0 | head -50"

result = phone.shell(cmd)

print(repr(result))
print("\n----\n")
print(result)