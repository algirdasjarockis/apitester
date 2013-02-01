# -*- coding: utf-8 -*-
# to run this test, use: python apitester example

from datetime import timedelta
import apitester

dbOpts = {
    "host": "amw",
    "productionDb": "amw",
    "testDb": "amw_test",
    "user": "root",
    "pass": "folnin",
    "dumpFile": "testapi-amw.sql",      # db dump file
    "dumpFileLifetime": 180             # time interval in seconds when dump must be regenarated
}


example = {
    "serverUrl": "http://user:pass@my-server.com/api/namespace",
    "db": dbOpts,
    "methods": {
        "Account.testMethod": {
            # int, int, string
            "args": [
                [],
                [0, 1, "test"],
                [1, 3, apitester.getDate()],
                [1337, 0, "leet"],
                [0, 0, "i dont care"]            
            ],
            "results": {
                "type": [
                    list,               # any array even empty
                    #str, int, float,    # str, int, float, ... any ordinary python type can be used                    
                    #[int, str],         # array which contains at least one int and str value
                    #[(5,)],             # array must contain >= 5 values
                    #[(str, 2), (int,1)],# array which contains at least 2 str and one int
                    #[(float,)]          # array which contains _only_ float (no additional values permitted)
                    #[({...},), ({...},)]# array which contains only given struct types, no additional types allowed
                    #(str, int, str),    # ordered array which holds str int str values in that order
                    None,
                    [int],
                    str,
                    {
                        # there is struct and must cointain given fields
                        "field1": int,
                        "field2": bool, 
                        "field3": [(int,5), (str,1)],
                        "complexField": {
                            "cField1": float,
                            "cField2": str,
                            "cField3": {
                                "ccField1": 0,  # any type
                                "ccField2": str
                            }
                        },
                        "dynamicField": {
                            str: {
                                "field0": int
                            },
                        }
                        
                    }
                ],
                
                # if this set, apitester should test these values first (only?)
                "Zvalues": [
                    # expected valid results for params #1
                    [
                        [1, 2, 1, 2, 1, 1, 2, 1],
                        ["wtf"],
                        ["omg"],
                        []
                    ],
                    # .. params #2
                    "u gave me 1, 3 and 'leet'"
                    ,
                    # .. params #3
                    {
                        "field1": 1337,
                        "field2": True,
                        "field3": [1, 3, 3, 7],
                        "complexField": {
                            "cField1": 0.01,
                            "cField2": "leet",
                            "cField3": {
                                "ccField1": 0,
                                "ccField2": "leet recursion"
                            }
                        }
                    },
                    # .. params #4
                    [
                        None # no result expected
                    ]
                ]
            }
        }
    }
}
 
