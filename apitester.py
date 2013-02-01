#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

if __name__ == "apitester":
    import MySQLdb
    from datetime import datetime, timedelta
    
    def apitesterFunc(param):
        print param
        print "This is apitester func! ({0})".format(__name__)
        
    #
    # Helper function for test file, that easily returns value from db
    #
    # @param struct dbOpts - db dict from test file
    # @param string table - table name
    # @param string field - field name, can be multiple fields separated in commas or asterisk,
    #                        result will be dict not single value
    # @param string where - some additional clauses like WHERE and ORDER
    # @return string | dict
    #
    def getDbValue(dbOpts, table, field, where = ''):
        conn = MySQLdb.connect( host = dbOpts['host'],
                            user = dbOpts['user'],
                            passwd = dbOpts['pass'],
                            db = dbOpts['productionDb'])

        db = conn.cursor(MySQLdb.cursors.DictCursor)
        whereClause = '';
        if where != '':
            whereClause = " WHERE " + where;
        db.execute("SELECT {0} FROM `{1}`{2}".format(field, table, whereClause))
        value = db.fetchone()
        
        if len(value) == 1:
            return value[field]
        else:
            return value
            
            
    #
    # Helper function for test file, that returns current date in string with give
    # format and timedelta
    #
    # @param datetime.timedelta tdelta - offset from current time
    # @param bool local - True if use local time
    # @param string format - date format
    #
    def getDate(tdelta = timedelta(minutes = 0), local = True, format = "%Y-%m-%d %H-%M-%S"):
        dt = 0
        if local:
            dt = datetime.now()
        else:
            dt = datetime.utcnow()
            
        dt += tdelta
            
        return dt.strftime(format)


elif __name__ == "__main__":
    import xmlrpclib
    import os, os.path, sys
    import subprocess
    import imp
    import time
    import argparse
    
    # argument parsing
    parser = argparse.ArgumentParser(prog="apitester", description='XML-RPC API tester')
    parser.add_argument('testfile')
    parser.add_argument('method', default='', nargs='?')
    parser.add_argument('--host', metavar="custom_host", help="Sets custom full API url")
    parser.add_argument('-t', '--tests-dir', metavar="tests_location", help="Sets tests files location, default = './tests'")
    parser.add_argument('-d', '--debug', action="store_true", help="Enables XML-RPC verbose mode")
    parser.add_argument('-c', '--create-test-db',  action="store_true", help="Force to dump and create test database")
    parser.add_argument('-m', '--import-sql', nargs='+', metavar="sql_file", help="Executes given SQL files to test database (works only if 'db' config section is provided)")
    parser.add_argument('--db-opts', nargs="+", metavar="db_opt", help="Override DB settings, values are given in format <name>:<value> where value names are same in testfile.db section")
    parser.add_argument('--auth-opts', nargs="+", metavar="auth_opt", help="Override auth settings, values are given in format <name>:<value> where value names are same in testfile.auth section")
    parser.add_argument('--import-to-production', action="store_true", help="Usable only when -m (--import-sql) used. Makes import to production db instead of test, use with caution")
    parser.add_argument('--ignore-db', action="store_true", help="Ignore and do not execute ANY DB operation")
    parser.add_argument('-e', '--exit-after-db', action="store_true", help="Exits after DB dump or import actions")
    
    # all stored arguments and flags are here
    args = parser.parse_args()
    print args
    #sys.exit(0)
    
    #
    # compare array types by given pattern
    #
    def compareArrayTypes(pattern, array, level = 0, h = []):
        # type positions
        arrayPos = {}   
        
        results = []   
        arrLen = len(array)
        padding = "\t"
        if level > 0:
            padding += ("  " * level) + "{0}: ".format(h)
        
        # order
        i = 0
        
        # analyze given array
        for item in array:
            itemType = type(item)
                       
            if itemType in arrayPos:
                arrayPos[itemType].append(i)
            else:
                arrayPos[itemType] = [i]
                
            i += 1
                
        # position of pattern
        i = 0
    
        if type(pattern) == list:
            # handle unordered lists
            for item in pattern:
                if type(item) == type:
                    # we got simple type in list
                    if not item in arrayPos:
                        results.append(padding + "There is no one value with required type ({0})".format(item))
                elif type(item) == tuple:
                    # we got definition, (n,) or (<type>, n) or very strict (<type>,)
                    if type(item[0]) == int:
                        # defined desired length of array
                        if arrLen < item[0]:
                            results.append(padding + "Array does not contain desired item count, required: {0}, got: {1}".format(item[0], arrLen))
                            
                    # (x,)
                    elif len(item) == 1:
                        if type(item[0]) == type:
                            if not item[0] in arrayPos:
                                results.append(padding + "Array does not contain desired type ({0}) of elements".format(item[0]))
                            elif len(arrayPos) > 1:
                                # we got more and not needed types
                                results.append(padding + "Array contains extra elements, only type ({0}) needed".format(item[0]))
                        if type(item[0]) == dict:
                            if not dict in arrayPos:
                                results.append(padding + "Array does not contain desired type ({0}) of elements".format(item[0]))
                            else:
                                #compareStructFields(item[0], )
                                pass                        
                          
                    # (x, n)  
                    elif type(item[0]) == type:
                        # defined desired count of specific type
                        if not item[0] in arrayPos:
                            results.append(padding + "There is no one value with required type ({0})".format(item[0]))
                        elif item[1] > len(arrayPos[item[0]]):
                            results.append(padding + "There no one desired minimum count of value with required"\
                                " type ({0}), required: {1}, got: {2}".format(item[0], item[1], len(arrayPos[item[0]]) ))   
                                
                elif type(item) == dict:
                    if not dict in arrayPos:
                        results.append(padding + "There is no one value with required type ({0})".format(dict))
                    else:
                        structResults = []
                        gotOne = False
                        for pos in arrayPos[dict]:
                            tempResults = compareStructFields(item, array[pos], level + 1, h + [i])
                            if len(tempResults) <= 0:
                                # we need only one valid struct here
                                gotOne = True
                                break
                            else:
                                structResults += tempResults
                                
                        if not gotOne:
                            results += structResults
    
        elif type(pattern) == tuple:
            patternLen = len(pattern)
            # handle ordered lists
            for item in pattern:
                if type(item) == type:
                    if not item in arrayPos:
                        results.append(padding + "There is no one value with required type ({0})".format(item)) 
                    else:
                        # check bounds
                        if i >= arrLen:
                            results.append(padding + "Array with required order is smaller than expected, max index: {0}".format(arrLen - 1))
                        elif type(array[i]) != item:
                            results.append(padding + "Index {0} does not contain required type ({1}), got ({2})".format(i, item, type(array[i])))
                elif type(item) == tuple or type(item) == list:
                    if type(array[i]) != list:
                        results.append(padding + "Index {0} does not contain required type ({1}), got ({2})".format(i, list, type(array[i])))
                    else:
                        # omg, recursion again
                        results += compareArrayTypes(item, array[i], level + 1, h + [i])
                        
                elif type(item) == dict:
                    if type(array[i]) != dict: 
                        results.append(padding + "Index {0} does not contain required type ({1}), got ({2})".format(i, dict, type(array[i])))
                    else:
                        results += compareStructFields(item, array[i], level + 1, h + [i])
                i += 1
            
        return results
    
    
    #
    # check given structs fields by given pattern
    #
    def compareStructFields(pattern, subject, level = 0, h = []):
        results = []
        padding = "\t"
        if level > 0:
            padding += ("  " * level) + "{0}: ".format(h)
            
        subjects = subject       
        if type(subject) != list:
            subjects = [subject]           
          
        for subject in subjects:
            res = []
            for k, v in pattern.items():
                values = []                
                if type(k) == type:
                    noOneOfThatType = True
                    for key in subject.keys():
                        if k == type(key):                            
                            noOneOfThatType = False
                            values.append(subject[key])
                    
                    if noOneOfThatType:
                        res.append(padding + "Field '{0}' is not required type '{1}'".format(key, k))
                            
                elif not k in subject:
                    res.append(padding + "Given struct doesn't have field '{0}'".format(k))
                    continue
                else:
                    values = [subject[k]]
                    
                # value checking
                for subj in values:
                    if type(v) == type:
                        if v == str:
                            if not isinstance(subj, basestring):
                                res.append(padding + "Given struct field '{0}' type does not match, expected ({1}), got ({2})"\
                                    .format(k, v, type(subj)))
                        elif v != type(subj) or (v == str and type(subj) != unicode):
                            res.append(padding + "Given struct field '{0}' type does not match, expected ({1}), got ({2})"\
                                .format(k, v, type(subj)))
                    elif type(v) == dict:
                        # zomg, recursion!
                        if type(subj) != dict:
                            res.append(padding + "Given struct field '{0}' type does not match, expected ({1}), got ({2})".format(k, v, type(subj)))
                        else:
                            res += compareStructFields(v, subj, level + 1, h + [k])
                    elif type(v) == list or type(v) == tuple:
                        if type(subj) != list:
                            res.append(padding + "Given struct field '{0}' type does not match, expected ({1}), got ({2})".format(k, v, type(subj)))
                        else:
                            arrResults = compareArrayTypes(v, subj)
                            if len(arrResults) > 0:
                                res.append(padding + "At {0}, got array check errors at provided indexes: ".format(k))
                                res += arrResults
                            
            if len(res) <= 0:
                return []
            else:
                results += res
                    
        return results
        

    moduleName = args.testfile
    testIdentifier = 'apitester00001'
    requestedMethod = args.method
    xmlrpcDebug = args.debug      
    testsDir = args.tests_dir
    
    if not testsDir:
        testsDir = "tests"   
    
    testFile = "{0}/{1}.py".format(testsDir, moduleName)
    try:
        mod = imp.load_source("test", testFile)
    except Exception as err:
        print("Can not load '{0}'".format(moduleName))
        print("  {0}".format(err))
        sys.exit(1)
    
    testcase = getattr(mod, moduleName)
    
    # db configuration
    dbOpts = None
    if "db" in testcase:
        dbOpts = testcase["db"]
        
        if args.db_opts:
            # override dbOpts from test file
            for value in args.db_opts:
                values = value.split(":")
                if len(values) == 2:
                    dbOpts[values[0]] = values[1]
                    
            mod.reinit(dbOpts)
                    
    
    # server url setting
    authOpts = None
    serverUrl = None
    if args.host:
        serverUrl = args.host    
    
    elif "serverUrl" in testcase:
        serverUrl = testcase["serverUrl"]
    elif "auth" in testcase:
        # watch out, we got badass auth struct here!
        authOpts = testcase["auth"]
        requiredFields = ["host", "path", "user", "pass", "protocol"]
        missingFields = []
        for field in requiredFields:
            if not field in authOpts:
                missingFields.append(field)
                
        if len(missingFields) > 0:
            print("Missing fields in 'auth' section:")
            for field in missingFields:
                print("\t" + field)
            
            # we can not continue since this test needs auth section set properly
            sys.exit(1)
            
        if args.auth_opts:
            # override auth from test file
            for value in args.auth_opts:
                values = value.split(":")
                if len(values) == 2:
                    authOpts[values[0]] = values[1]
                    
        # construct url
        serverUrl = "{proto}://{usr}:{passw}@{host}/{path}".\
            format(proto=authOpts['protocol'], usr=authOpts['user'], passw=authOpts['pass'], host=authOpts['host'], path=authOpts['path'])

    print("Using: {0}".format(serverUrl))
    srv = xmlrpclib.ServerProxy(serverUrl, verbose=xmlrpcDebug, encoding="utf-8")
       
    if not args.ignore_db:
        if dbOpts:       
            # check if required fields are here
            requiredFields = ["host", "productionDb", "testDb", "user", "pass",
                "dumpFile", "dumpFileLifetime"]
                
            missingFields = []
            for field in requiredFields:
                if not field in dbOpts:
                    missingFields.append(field)
                    
            if len(missingFields) > 0:
                print("Missing fields in 'db' section:")
                for field in missingFields:
                    print("\t" + field)
                
                # we can not continue since this test needs db and is not properly set up
                sys.exit(1)
                               
            externalTools = ["mysql", "mysqldump"]
            missingTools = []
            #for tool in externalTools:
            #    out = subprocess.check_output(["whereis", tool]).split(":")
            #    if len(out) <= 1 or len(out[1].strip(" ")) < len(tool):
            #        missingTools.append(tool)
        
            if len(missingTools) > 0:
                print("Missing required external tools:")
                for tool in missingTools:
                    print("\t" + tool)
                sys.exit(1)
                
            # preventing massive disaster :-)
            if dbOpts["productionDb"] == dbOpts["testDb"]:
                print("Production DB can not be same as testing DB! Exiting...")
                sys.exit(2)
            
            # main db job
            try:
                res = os.stat(dbOpts["dumpFile"])
                mtime = res.st_mtime // 1
                if (time.time() // 1) - mtime > int(dbOpts["dumpFileLifetime"]):
                    raise Exception("Dump file is too old")
                elif args.create_test_db:
                    raise Exception("Requested DB dump")
            except Exception as err:
                print(err)
               
                # make new sql dump 
                print("- Creating database dump")       
                out = subprocess.call("mysqldump -h {0} -u {1} -p{2} {3} > {4}".format(
                    dbOpts['host'], dbOpts["user"], dbOpts["pass"], dbOpts["productionDb"], dbOpts["dumpFile"] 
                ), shell=True)
                
                if out != 0:
                    print("\tDump failed! Exiting...")
                    sys.exit(out)
        
                        
                # drop test database
                out = subprocess.call("mysql -h {0} -u {1} -p{2} -e 'DROP DATABASE {3}'".format(
                    dbOpts['host'], dbOpts["user"], dbOpts["pass"], dbOpts["testDb"]
                ), shell=True)
                
                # create test database
                out = subprocess.call("mysql -u {0} -p{1} -e 'CREATE DATABASE {2}'".format(
                    dbOpts["user"], dbOpts["pass"], dbOpts["testDb"]
                ), shell=True)
                
                if out != 0:
                    print("\tCan not create test DB!")
                    sys.exit(out)        
        
                # fill up test db
                out = subprocess.call("mysql -u {0} -p{1} {2} < {3}".format(
                    dbOpts["user"], dbOpts["pass"], dbOpts["testDb"], dbOpts["dumpFile"]
                ), shell=True)
                
                if out != 0:
                    print("\tCan not import DB!")
                    sys.exit(out)
                    
                print("- Test DB import is succesfull")
            else:
                print("- Using previous DB dump {0}".format(dbOpts["dumpFile"]))
            finally:
                if args.import_sql:
                    destDb = dbOpts["testDb"]
                    if args.import_to_production:
                        destDb = dbOpts["productionDb"]
                        
                    print("- Importing custom SQL files to '{0}'".format(destDb))
                    for sqlFile in args.import_sql:
                        out = subprocess.call("mysql -u {0} -p{1} {2} < {3}".format(
                            dbOpts["user"], dbOpts["pass"], destDb, sqlFile), shell=True
                        )
                        if out != 0:
                            print("\tFailed!")
                    
                if args.exit_after_db:
                    sys.exit(0)
                
        # if was requested to do db job only
        elif not args.create_test_db:
            print("Can not dump database cause of no 'db' config section provided in given testfile '{0}'".format(moduleName))
            sys.exit(1)
        
    
    # statistics
    stats = {
        "testsCount": 0,
        "testsPassed": 0,
        "testsFailed": 0
    }
    
    testcase = mod.initTest()
    
    # checking what database API uses 
    if dbOpts:
        currentDb = srv.__testGetDbName(testIdentifier)
        if currentDb != dbOpts['testDb']:
            print("API uses non test DB '{0}'!".format(currentDb))
            sys.exit(1)
    
    methodsOrdered = testcase["methods"].keys()
    methodsOrdered.sort()
           
    # method iteration
    #for methodName, method in testcase["methods"].items():
    for methodName in methodsOrdered:
        method = testcase["methods"][methodName]
        # dealing with blabla:method names
        m = methodName.split(":")
        if len(m) > 1:
            methodName = m[1]
        else:
            methodName = m[0]
            
        if requestedMethod != '' and methodName != requestedMethod:
            continue
            
        print("\nTesting method '{0}'...".format(methodName))        
        
        # argument iteration
        i = 0
        for arg in method["args"]:
            stats["testsCount"] += 1
            
            try:          
                result = getattr(srv, methodName)(*arg)
                
                if isinstance(result, basestring):
                    result = result.encode("utf-8")
                
                failed = True
                
                if "values" in method["results"]:
                    # check values first
                    resultCount = len(method["results"]["values"])
                    expResults = method["results"]["values"][0]
                    if resultCount > 1:
                        expResults = method["results"]["values"][i]
                    
                    # if we got multiple possible valid results
                    if (type(expResults) == list):
                        for expResult in expResults:
                            if result == expResult:
                                # found one correct, that's enough for good test
                                failed = False
                                break
                    else:
                        if result == expResults:
                            failed = False
                            
                    if failed:
                        stats["testsFailed"] += 1
                        print("\t#{0}: Failed with param set: {1}".format(i, arg))
                        if type(expResults) == list:
                            print("\t#{0}: - expected with one of these: ".format(i))
                            for expResult in expResults:
                                print("\t\t {0}".format(expResult))
                        else:
                            print("\t#{0}: - expected with ({1}): ".format(i, expResults))
                                
                        print("\t#{0}: - got ({1})".format(i, result))                    
                    else:
                        stats["testsPassed"] += 1
                        
                elif "type" in method["results"]:
                    results = []
                    for dType in method["results"]["type"]:
                        if type(dType) == dict and type(result) == dict:
                            # we got badass struct here
                            #print "--- Checking: {0} vs {1}".format(dType, result)
                            results = compareStructFields(dType, result)
                            if len(results) <= 0:
                                failed = False
                            elif len(result) > 0:
                                failed = True
                        if (type(dType) == list or type(dType) == tuple) and type(result) == list:
                            results = compareArrayTypes(dType, result)
                            if len(results) <= 0:
                                # if failed and result was not empty, we should 'report' this :-)
                                failed = False
                            elif len(result) > 0:
                                # if failed and result was not empty, we should 'report' this too
                                failed = True
                        elif type(dType) == type:
                            if type(result) == dType:
                                failed = False
                        elif dType == None and result == None:
                            failed = False
    
    
                    if failed:
                        stats["testsFailed"] += 1
                        print("\t#{0}: Failed with param set: {1}, type mismatch".format(i, arg))
                        print("\t#{0}: - got ({1})".format(i, result))
                        for res in results:
                            print res             
                    else:
                        stats["testsPassed"] += 1
     
                
            except Exception as err:
                print("\t#{0} Exception: {1}, params: {2}".format(i, err, arg))
                try:
                    print("\t{0}".format(result))
                except: pass
                stats["testsFailed"] += 1
                
            i += 1
    
    print("\n")
    print("-" * 78)
    print(" TESTS FINISHED")
    print("-" * 78)
    
    print(" Methods count: {0}".format(len(testcase["methods"])))
    print(" Tests count: {0}".format(stats["testsCount"]))
    print(" Tests passed: {0}".format(stats["testsPassed"]))
    print(" Tests failed: {0}".format(stats["testsFailed"]))
    
    if stats["testsFailed"] > 0:
        sys.exit(2)












