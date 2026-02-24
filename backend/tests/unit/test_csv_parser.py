import datetime
from decimal import Decimal
from io import BytesIO

import pytest

from src.schemas.data_import import ParsedTransaction  # AccountType used in assertions
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
        # charset_normalizer returns 'ascii' for pure ASCII content, which is valid
        assert CsvParser.detect_encoding(BytesIO(content_utf8)) in ["utf-8", "ascii"]

        content_big5 = "測試".encode("big5")
        assert CsvParser.detect_encoding(BytesIO(content_big5)) == "big5"


class TestMyAbCsvParser:
    def test_parse_valid_csv(self, myab_csv_file):
        parser = MyAbCsvParser()
        transactions, errors = parser.parse(myab_csv_file)
        assert len(errors) == 0

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
        transactions, errors = parser.parse(BytesIO(content))
        assert len(errors) > 0
        assert "Invalid date format" in errors[0].message

    def test_parse_invalid_amount(self):
        content = """日期,交易類型,支出科目,收入科目,從科目,到科目,金額,明細,發票號碼
2024/01/01,支出,E-Food,,,A-Cash,invalid,Desc,""".encode()
        parser = MyAbCsvParser()
        transactions, errors = parser.parse(BytesIO(content))
        assert len(errors) > 0
        assert "Invalid amount format" in errors[0].message


# T043: Unit test for credit card CSV parser (multiple banks)
# T045: Unit test for bank config loading

SAMPLE_CATHAY_CSV = """2026/02信用卡對帳單
帳單資訊,,,

帳單明細
新臺幣
"消費日","交易說明","新臺幣金額","卡號/行動末四碼","消費國家/幣別","消費金額","入帳起息日","折算日"
"−","上期帳單總額","112,297","−","−","−","−","−"
"02/03","ＣＵＢＥＡｐｐ轉帳繳款","-112,297","9341","−","−","02/03","−"
"01/15","星巴克信義店","150","9341","TW / TWD","−","01/21","−"
"01/16","全聯福利中心","520","9341","TW / TWD","−","01/22","−"
"12/25","跨年測試消費","300","9341","TW / TWD","−","01/01","−"
"正卡消費 TWD 96210"
""".encode()

SAMPLE_CTBC_CSV = """交易日,商店,消費金額
2024-01-10,台北101美食街,280
2024-01-12,中油加油站,1200
""".encode()


class TestBankConfigLoading:
    """T045: Unit test for bank config loading"""

    def test_get_supported_banks(self):
        from src.services.bank_configs import get_supported_banks

        banks = get_supported_banks()
        assert len(banks) >= 5  # 至少支援 5 家銀行
        bank_codes = [b.code for b in banks]
        assert "CATHAY" in bank_codes
        assert "CTBC" in bank_codes
        assert "ESUN" in bank_codes
        assert "TAISHIN" in bank_codes
        assert "FUBON" in bank_codes

    def test_get_bank_config(self):
        from src.services.bank_configs import get_bank_config

        config = get_bank_config("CATHAY")
        assert config is not None
        assert config.code == "CATHAY"
        assert config.name == "國泰世華"
        assert config.date_column >= 0
        assert config.amount_column >= 0
        assert config.description_column >= 0

    def test_get_bank_config_not_found(self):
        from src.services.bank_configs import get_bank_config

        config = get_bank_config("UNKNOWN_BANK")
        assert config is None


class TestCreditCardCsvParser:
    """T043: Unit test for credit card CSV parser (multiple banks)"""

    def test_parse_cathay_csv(self):
        from src.schemas.data_import import AccountType
        from src.services.csv_parser import CreditCardCsvParser

        parser = CreditCardCsvParser("CATHAY")
        transactions, errors = parser.parse(BytesIO(SAMPLE_CATHAY_CSV))
        assert len(errors) == 0

        # Should skip: "−" date row (上期帳單總額) and negative amount row (繳款)
        # Should parse: 3 actual purchase transactions
        assert len(transactions) == 3

        # tx1: bill month 2026/02, tx month 01 <= 02 → year 2026
        tx1 = transactions[0]
        assert tx1.date == datetime.date(2026, 1, 15)
        assert tx1.amount == Decimal("150")
        assert tx1.description == "星巴克信義店"
        # Account path types must be correctly set
        assert tx1.from_account_path is not None
        assert tx1.from_account_path.account_type == AccountType.LIABILITY
        assert tx1.to_account_path is not None
        assert tx1.to_account_path.account_type == AccountType.EXPENSE

        tx2 = transactions[1]
        assert tx2.date == datetime.date(2026, 1, 16)
        assert tx2.amount == Decimal("520")
        assert tx2.description == "全聯福利中心"

        # tx3: bill month 2026/02, tx month 12 > 02 → cross-year → year 2025
        tx3 = transactions[2]
        assert tx3.date == datetime.date(2025, 12, 25)
        assert tx3.amount == Decimal("300")
        assert tx3.description == "跨年測試消費"

    def test_cathay_skips_payment_rows(self):
        """Negative-amount (payment) rows must be filtered out."""
        from src.services.csv_parser import CreditCardCsvParser

        parser = CreditCardCsvParser("CATHAY")
        transactions, errors = parser.parse(BytesIO(SAMPLE_CATHAY_CSV))
        descriptions = [tx.description for tx in transactions]
        assert "ＣＵＢＥＡｐｐ轉帳繳款" not in descriptions
        assert "上期帳單總額" not in descriptions

    def test_cathay_year_inference_cross_year(self):
        """Transaction month > bill month must resolve to previous year."""
        from src.services.csv_parser import CreditCardCsvParser

        parser = CreditCardCsvParser("CATHAY")
        transactions, _errors = parser.parse(BytesIO(SAMPLE_CATHAY_CSV))
        cross_year_tx = next(tx for tx in transactions if tx.description == "跨年測試消費")
        assert cross_year_tx.date.year == 2025
        assert cross_year_tx.date.month == 12

    def test_parse_ctbc_csv(self):
        from src.services.csv_parser import CreditCardCsvParser

        parser = CreditCardCsvParser("CTBC")
        transactions, errors = parser.parse(BytesIO(SAMPLE_CTBC_CSV))
        assert len(errors) == 0

        assert len(transactions) == 2

        tx1 = transactions[0]
        assert tx1.date == datetime.date(2024, 1, 10)
        assert tx1.amount == Decimal("280")
        assert tx1.description == "台北101美食街"

    def test_parse_unsupported_bank(self):
        from src.services.csv_parser import CreditCardCsvParser

        with pytest.raises(ValueError, match="Unsupported bank"):
            CreditCardCsvParser("UNKNOWN_BANK")

    def test_parse_invalid_format(self):
        from src.services.csv_parser import CreditCardCsvParser

        # CATHAY format with enough columns but an invalid date value
        invalid_csv = (
            "2026/02信用卡對帳單\n"
            '"消費日","交易說明","新臺幣金額","卡號/行動末四碼"\n'
            '"99/99","無效日期店家","150","9341"\n'
        ).encode()

        parser = CreditCardCsvParser("CATHAY")
        transactions, errors = parser.parse(BytesIO(invalid_csv))
        assert len(errors) > 0
