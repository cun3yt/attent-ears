from django.utils import timezone

timezone.activate('America/Los_Angeles')
now = timezone.localtime(timezone.now()).strftime("%Y-%m-%d %H:%M:%S")
*_, filename = __file__.split('/')

print("{} is ran at {}".format(filename, now))
