from parser import Parser

if __name__ == "__main__":
    parser = Parser()
    parser.set_tennis()
    parser.run(parser.refresh_coefficients())
