import unicodedata

def name(name):
  if name is None:
    return None
  ascii_name = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore')
  return ascii_name.strip().upper().decode('ascii')

def phone(phone):
  if phone is None:
    return None
  return ''.join(filter(lambda x: x.isdigit(), phone.strip()))

def address(address):
  if address is None:
    return None
  ascii_address = unicodedata.normalize('NFKD', address).encode('ascii', 'ignore')
  return ascii_address.strip().upper().decode('ascii')

def zip(zip):
  if zip is None:
    return None
  return zip.strip()

def email(email):
  if email is None:
    return None
  ascii_email = unicodedata.normalize('NFKD', email).encode('ascii', 'ignore')
  return ascii_email.strip().upper().decode('ascii')