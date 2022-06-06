import sys
from datetime import datetime, timedelta
import utils.utils as utils
from mysql.connector import connect

# testing
#start_date = '2022-01-01'
#end_date = datetime.strftime(datetime.today(), '%Y-%m-%d')
environment = 'dev'

config_file = './cfg/config_private.json'
config = utils.get_session_config(config_file)

# valid_start_date = utils.validate_input_date(start_date)
##valid_end_date = utils.validate_input_date(end_date)
##valid_environment = utils.validate_environment(environment)
##
###if not valid_start_date or not valid_end_date:
##if not valid_end_date:
##    error_message = "Invalid date format. Use 'm/d/yyyy'."
##    utils.exit_on_error(error_message)
##
##if not valid_environment:
##    error_message = "Invalid environment '" + str(environment) + "' passed to sys.argv[3]."
##    utils.exit_on_error(error_message)

connection_config = config['mySQL']['connection_config']
conn = connect(host=connection_config['hostname'],
                                database=connection_config['db'],
                                user=connection_config['username'],
                                password=connection_config['password'])


cutoff_date, start_date, end_date = utils.get_setup_dates(conn, config['mySQL']['insert_tables'][environment])
