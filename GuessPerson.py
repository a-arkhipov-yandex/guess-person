from typing import Literal
from db_lib import *
from log_lib import *
from GuessPersonBot import *

#===============
# Main section
#---------------
def main() -> Literal[0]:
    initLog()
    TESTCONNECTION = isTestDB()
    log(str=f'Test DB = {TESTCONNECTION}',logLevel=LOG_DEBUG)
    Connection.initConnection(test=TESTCONNECTION)
    bot = GuessPersonBot()
    if (not GuessPersonBot.isInitialized()):
        log(str=f'Error initializing bot. Exiting...')
        exit(code=0)
    # Start bot
    bot.startBot()
    Connection.closeConnection()
    closeLog()
    return 0

if __name__ == "__main__":
    main()