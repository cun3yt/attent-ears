from email_split import email_split

personal_email_domains = [
    "gmail.com", "yahoo.com", "yahoo.co.in", "aol.com", "att.net", "comcast.net",
    "facebook.com", "gmail.com", "gmx.com", "googlemail.com", "google.com", "hotmail.com", "hotmail.co.uk",
    "mac.com", "me.com", "mail.com", "msn.com", "live.com", "sbcglobal.net", "verizon.net", "yahoo.com",
    "yahoo.co.uk", "rediif.com"
]


def is_email_address_in_domain(email_address, email_domain):
    email = email_split(email_address)
    return email.domain == email_domain


def is_email_address_personal(email_address):
    email = email_split(email_address)
    return email.domain in personal_email_domains
