from django.utils import timezone


def print_current_datetime():
    timezone.activate('America/Los_Angeles')
    now = timezone.localtime(timezone.now()).strftime("%Y-%m-%d %H:%M:%S")
    *_, filename = __file__.split('/')

    print("{} is ran at {}".format(filename, now))


def run():
    print_current_datetime()
