import getopt
import sys

loglevel = 'WARNING'

try:
    options, remainder = getopt.gnu_getopt(sys.argv[1:], '', ['loglevel='])

except getopt.GetoptError as err:
    print('pifire: Invalid command line:', err)
    sys.exit(1)

for opt, arg in options:
    if opt in ('--loglevel'):
        loglevel = arg

print('LOGLEVEL   :', loglevel)
print('REMAINING :', remainder)
