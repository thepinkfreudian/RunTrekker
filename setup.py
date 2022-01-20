import sys
from datetime import datetime, timedelta
import utils.utils as utils

###start_date = sys.argv[1]
##end_date = sys.argv[1]
##environment = sys.argv[2]

# testing
start_date = '2022-01-01'
end_date = '2022-01-20'
environment = 'dev'


push = False
if len(sys.argv) > 3:
    if sys.argv[3] == 'push':
        push = True
    else:
        error_message = "Invalid argument '" + str(sys.argv[3]) + "' passed to sys.argv[4]."
        utils.exit_on_error(error_message)

# valid_start_date = utils.validate_input_date(start_date)
valid_end_date = utils.validate_input_date(end_date)
valid_environment = utils.validate_environment(environment)

#if not valid_start_date or not valid_end_date:
if not valid_end_date:
    error_message = "Invalid date format. Use 'm/d/yyyy'."
    utils.exit_on_error(error_message)

if not valid_environment:
    error_message = "Invalid environment '" + str(environment) + "' passed to sys.argv[3]."
    utils.exit_on_error(error_message)

# set global session variables
lookback_days = timedelta(7)
#start_date = datetime.strftime(datetime.strptime(end_date, '%m/%d/%Y') - lookback_days, '%m/%d/%Y')
config_file = './cfg/config_private.json'
config = utils.get_session_config(config_file)

