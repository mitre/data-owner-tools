from secrets import token_hex

# use 32 characters (1 character = 4 bits) for 128 bits of entropy
deidentification_secret = token_hex(32)

with open('deidentification_secret.txt', 'w', newline='') as secret_file:
  secret_file.write(deidentification_secret)
