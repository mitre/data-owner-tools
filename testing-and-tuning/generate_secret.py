from secrets import token_hex

secret_bit_length = 128

deidentification_secret = token_hex(secret_bit_length)

with open('deidentification_secret.txt', 'w', newline='') as secret_file:
  secret_file.write(deidentification_secret)
