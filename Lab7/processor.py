def parse_int_list(s):
    return [int(x) for x in s.split(',')]

def calculate_discount(price, discount):
    return price - (price * discount / 100)

def process_user_data(data):
    return data.get("username").strip().lower()

if __name__ == "__main__":
    print("Running processor...")
    print(parse_int_list("1,2,3"))
    print(calculate_discount(100, 10))
    print(process_user_data({"username": "  ADMIN  "}))
