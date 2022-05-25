from application import main
import os
import pytest

class TestClass:

    cwd = os.path.dirname(__file__)
    def base(self,test_name):
        print(test_name)


    @pytest.mark.parametrize('args,expected',[([],'Input requires'),
                                            ([cwd],'Input requires'),
                                            (['','01/05/2021'],'not a valid directory'),
                                            ([cwd,''],'empty'),
                                            ([cwd + '\\error',''],'is not a valid directory'),
                                            ([cwd,'2022/05/01'],'Encountered a value error'),
                                            ([cwd+'\\tests','01/05/2022'],'')])
    def test_app_inputs_double_missing(self,args,expected):
        self.base(__name__)
        out = main(args)
        assert expected in out

    
