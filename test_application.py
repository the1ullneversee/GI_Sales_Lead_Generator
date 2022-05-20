from application import *
import os
import pytest

class TestClass:

    cwd = os.path.dirname(__file__)
    def base(self,test_name):
        print(test_name)
    #test that the application returns appropriate message if double arguments are missing
    def test_app_inputs_double_missing(self):
        self.base(__name__)
        args = []
        out = main(args)
        assert 'Input requires' in out

    #test that the application returns appropriate message if 1 arguement is  missing
    def test_app_inputs_single_missing(self):
        self.base(__name__)
        args = [TestClass.cwd]
        out = main(args)
        assert 'Input requires' in out

    #test that the application returns appropriate message if 1 arguement is  missing
    def test_app_inputs_no_directory(self):
        self.base(__name__)
        args = ['','01/05/2021']
        out = main(args)
        assert 'not a valid directory' in out

    #test that the application returns appropriate message if 1 arguement is  missing
    def test_app_inputs_no_date(self):
        self.base(__name__)
        args = [TestClass.cwd,'']
        out = main(args)
        assert 'empty' in out

    #test that the application returns appropriate validation message
    def test_app_inputs_bad_directory(self):
        self.base(__name__)
        args = [TestClass.cwd + '\\error','']
        out = main(args)
        assert 'is not a valid directory' in out


    #test that the application returns appropriate message if 1 arguement is  missing
    def test_app_inputs_bad_date(self):
        self.base(__name__)
        #this is a bad date as it does not conform to the application specification!
        args = [TestClass.cwd,'2022/05/01']
        out = main(args)

        assert 'Encountered a value error' in out
    
    #test that the application returns appropriate message if 1 arguement is  missing
    def test_app_bad_csv_files(self):
        self.base(__name__)

        #this is a bad date as it does not conform to the application specification!
        args = [TestClass.cwd+'\\tests','01/05/2022']
        out = main(args)

        print(out)
        assert out == ""
    

    
