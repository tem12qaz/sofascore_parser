from parser import Parser

if __name__ == "__main__":
    parser = Parser()
    parser.set_football()
    # parser.run(parser.refresh_coefficients())
    parser.run(parser.run_write())

