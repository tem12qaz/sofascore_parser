from parser import Parser

if __name__ == "__main__":
    parser = Parser(last_day_str='2023-01-10')
    parser.set_tennis()
    parser.init_workbook()
    parser.run()