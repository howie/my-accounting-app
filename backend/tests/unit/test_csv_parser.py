import datetime
from decimal import Decimal
from io import BytesIO

import pytest

from src.schemas.data_import import ParsedTransaction
from src.services.csv_parser import CsvParser, MyAbCsvParser

# T012: Unit test for MyAB CSV parser
# T013: Unit test for date format parsing
# T014: Unit test for amount format parsing

SAMPLE_MYAB_CSV = """日期,交易類型,支出科目,收入科目,從科目,到科目,金額,明細,發票號碼
2024/01/01,支出,E-餐飲費,,A-現金,,100,午餐,AB12345678
2024-01-02,收入,,I-薪資,,A-銀行,"50,000",Salary,
01/03/2024,轉帳,,,A-銀行,L-信用卡,"5,000.50",Bill,
""".encode()


@pytest.fixture
def myab_csv_file():
    return BytesIO(SAMPLE_MYAB_CSV)


class TestCsvParserUtils:
    def test_detect_encoding(self):
        content_utf8 = b"test"
        assert CsvParser.detect_encoding(BytesIO(content_utf8)) == "utf-8"

        content_big5 = "測試".encode("big5")
        assert CsvParser.detect_encoding(BytesIO(content_big5)) == "big5"


class TestMyAbCsvParser:
    def test_parse_valid_csv(self, myab_csv_file):
        parser = MyAbCsvParser()
        transactions = parser.parse(myab_csv_file)

        assert len(transactions) == 3

        # Row 1: 2024/01/01 (yyyy/MM/dd)
        tx1 = transactions[0]
        assert isinstance(tx1, ParsedTransaction)
        assert tx1.date == datetime.date(2024, 1, 1)
        assert tx1.amount == Decimal("100")
        assert tx1.description == "午餐"
        assert tx1.invoice_number == "AB12345678"
        assert tx1.from_account_name == "A-現金"
        assert tx1.to_account_name == "E-餐飲費"

        # Row 2: 2024-01-02 (yyyy-MM-dd) + Amount with comma
        tx2 = transactions[1]
        assert tx2.date == datetime.date(2024, 1, 2)
        assert tx2.amount == Decimal("50000")

        # Row 3: 01/03/2024 (MM/dd/yyyy - assuming US format or just flexible)
        # Spec says "yyyy/MM/dd, yyyy-MM-dd, MM/dd/yyyy"
        tx3 = transactions[2]
        assert tx3.date == datetime.date(2024, 1, 3)
        assert tx3.amount == Decimal("5000.50")

    def test_parse_invalid_date(self):
        content = """日期,交易類型,支出科目,收入科目,從科目,到科目,金額,明細,發票號碼
invalid_date,支出,E-Food,,,A-Cash,100,Desc,""".encode()
        parser = MyAbCsvParser()
        with pytest.raises(ValueError, match="Invalid date format"):
            parser.parse(BytesIO(content))

    def test_parse_invalid_amount(self):
        content = """日期,交易類型,支出科目,收入科目,從科目,到科目,金額,明細,發票號碼
2024/01/01,支出,E-Food,,,A-Cash,invalid,Desc,""".encode()
        parser = MyAbCsvParser()
        with pytest.raises(ValueError, match="Invalid amount format"):
            parser.parse(BytesIO(content))
