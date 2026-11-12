from hypothesis import given, strategies as st
from processor import parse_int_list, calculate_discount, process_user_data

@given(st.text())
def test_parse_int_list_fuzz(s):
    try:
        parse_int_list(s)
    except Exception as e:
        pass

@given(st.floats(min_value=0, max_value=1000), st.floats(min_value=0, max_value=100))
def test_calculate_discount_fuzz(price, discount):
    try:
        calculate_discount(price, discount)
    except Exception as e:
        pass

@given(st.dictionaries(st.text(), st.text()))
def test_process_user_data_fuzz(data):
    try:
        process_user_data(data)
    except Exception as e:
        pass
