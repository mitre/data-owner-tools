import os
from zipfile import ZipFile

schema = ['name-sex-dob-zip.json', 'name-sex-dob-phone.json', 'name-sex-dob-addr.json']
command = "clkutil hash {source_file} {secret_one} {secret_two} {schema_path} {output_file}"

schema_dir = '/Users/andrewg/projects/anonlink-multiparty/data/mulit-round/siblings/'
source_file = '/Users/andrewg/projects/anonlink-multiparty/data/siblings/system-a.csv'
secret_one = 'foo'
secret_two = 'bar'
clk_files = []

if not os.path.exists('output'):
  os.mkdir('output')

for s in schema:
  schema_path = schema_dir + s
  output_file = 'output/' + s.replace('.json', '') + '.json'
  to_execute = command.format(source_file=source_file, secret_one=secret_one,
    secret_two=secret_two, schema_path=schema_path, output_file=output_file)
  os.system(to_execute)
  clk_files.append(output_file)

with ZipFile('garbled.zip', 'w') as garbled_zip:
  for clk_file in clk_files:
    garbled_zip.write(clk_file)
