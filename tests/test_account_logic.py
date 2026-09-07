import unittest

from gmail_automation import build_account_payload, gender_option_value, normalize_name, random_birthday


class AccountPayloadTests(unittest.TestCase):
    def test_normalize_name_removes_accents(self):
        self.assertEqual(normalize_name("José"), "jose")
        self.assertEqual(normalize_name("Álvaro"), "alvaro")

    def test_build_account_payload_uses_custom_values(self):
        payload = build_account_payload(
            first_name="John",
            last_name="Smith",
            username="john.smith",
            birthday="12 5 1990",
            gender="male",
            password="TestPass!123"
        )

        self.assertEqual(payload["first_name"], "John")
        self.assertEqual(payload["last_name"], "Smith")
        self.assertEqual(payload["username"], "john.smith")
        self.assertEqual(payload["birthday"], "12 5 1990")
        self.assertEqual(payload["gender"], "male")
        self.assertEqual(payload["password"], "TestPass!123")

    def test_random_birthday_returns_valid_format(self):
        birthday = random_birthday()
        parts = birthday.split()
        self.assertEqual(len(parts), 3)
        self.assertTrue(parts[0].isdigit())
        self.assertTrue(parts[1].isdigit())

    def test_gender_option_values_are_language_independent(self):
        self.assertEqual(gender_option_value("female"), "1")
        self.assertEqual(gender_option_value("male"), "2")
        self.assertEqual(gender_option_value("other"), "3")
        self.assertEqual(gender_option_value("custom"), "4")
        self.assertEqual(gender_option_value("unknown"), "3")
        self.assertTrue(parts[2].isdigit())


if __name__ == "__main__":
    unittest.main()
