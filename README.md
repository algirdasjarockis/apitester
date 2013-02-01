apitester
=========

XML-RPC API Tester

This apitester simply calls defined api methods in test file and checks returned values for types and result.
It's heavily depending on MySQL cause of this tool was made at my work for testing my own xmlrpc APIs written in PHP.
95% of API's methods were depending on data stored in MySQL server, so one of main task of apitester is to make
mysql dumps and copies and set initial business logics properly to achieve best efficiency in testing those
API's methods.

It is command line tool, help text is below:

<code>
XML-RPC API tester

positional arguments:
  testfile
  method

optional arguments:
  -h, --help            show this help message and exit
  --host custom_host    Sets custom full API url
  -t tests_location, --tests-dir tests_location
                        Sets tests files location, default = './tests'
  -d, --debug           Enables XML-RPC verbose mode
  -c, --create-test-db  Force to dump and create test database
  -m sql_file [sql_file ...], --import-sql sql_file [sql_file ...]
                        Executes given SQL files to test database (works only
                        if 'db' config section is provided)
  --db-opts db_opt [db_opt ...]                                                                                                                                                                                                                                                
                        Override DB settings, values are given in format                                                                                                                                                                                                       
                        <name>:<value> where value names are same in                                                                                                                                                                                                           
                        testfile.db section                                                                                                                                                                                                                                    
  --auth-opts auth_opt [auth_opt ...]                                                                                                                                                                                                                                          
                        Override auth settings, values are given in format                                                                                                                                                                                                     
                        <name>:<value> where value names are same in                                                                                                                                                                                                           
                        testfile.auth section                                                                                                                                                                                                                                  
  --import-to-production                                                                                                                                                                                                                                                       
                        Usable only when -m (--import-sql) used. Makes import                                                                                                                                                                                                  
                        to production db instead of test, use with caution                                                                                                                                                                                                     
  --ignore-db           Ignore and do not execute ANY DB operation                                                                                                                                                                                                             
  -e, --exit-after-db   Exits after DB dump or import actions     
</code>
