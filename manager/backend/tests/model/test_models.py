from django.test import TestCase

from ...models import TaggUser


class ModelTest(TestCase):
    def setUp(self):
        self.user = TaggUser.objects.create(
            username="john_123",
            password="taggPassword@123",
            first_name="John",
            last_name="Clark, Jr.",
            email="jclark12@gmail.com",
        )
        return super().setUp()

    def tearDown(self):
        return super().tearDown()

    def test_tagg_userModel(self):
        self.assertEqual(self.user.first_name, "John")
        self.assertEqual(self.user.last_name, "Clark, Jr.")
        self.assertEqual(self.user.username, "john_123")
        self.assertEqual(self.user.email, "jclark12@gmail.com")
        self.assertEqual(self.user.password, "taggPassword@123")

    def test_valid_firstnames(self):
        firstnames = ["John", "Foo", "a" * 20, "aa", "a-", "a'", "a.", "a,"]
        for name in firstnames:
            errors = TaggUser.objects.is_firstname_valid({"first_name": name})
            self.assertTrue(len(errors) == 0)

    def test_invalid_firstnames(self):
        error_msg = "First name is required"
        # missing key
        errors = TaggUser.objects.is_firstname_valid({})
        self.assertTrue(len(errors) == 1)
        self.assertTrue("first_name" in errors)
        self.assertEqual(errors["first_name"], error_msg)
        # empty field
        errors = TaggUser.objects.is_firstname_valid({"first_name": ""})
        self.assertTrue(len(errors) == 1)
        self.assertTrue("first_name" in errors)
        self.assertEqual(errors["first_name"], error_msg)

    def test_invalid_firstname2(self):
        error_msg = (
            "First name should be 2 to 20 characters and "
            "can contain dashes, apostrophe, periods and comma"
        )
        names = ["a", "a" * 21, "a0", "a_"]
        for name in names:
            errors = TaggUser.objects.is_firstname_valid({"first_name": name})
            self.assertTrue(len(errors) == 1)
            self.assertTrue("first_name" in errors)
            self.assertEqual(errors["first_name"], error_msg)

    def test_valid_lastnames(self):
        lastnames = ["John", "Foo", "a" * 20, "aa", "a-", "a'", "a.", "a,"]
        for name in lastnames:
            errors = TaggUser.objects.is_lastname_valid({"last_name": name})
            self.assertTrue(len(errors) == 0)

    def test_invalid_lastnames(self):
        error_msg = "Last name is required"
        # missing key
        errors = TaggUser.objects.is_lastname_valid({})
        self.assertTrue(len(errors) == 1)
        self.assertTrue("last_name" in errors)
        self.assertEqual(errors["last_name"], error_msg)
        # empty field
        errors = TaggUser.objects.is_lastname_valid({"last_name": ""})
        self.assertTrue(len(errors) == 1)
        self.assertTrue("last_name" in errors)
        self.assertEqual(errors["last_name"], error_msg)

    def test_invalid_lastname2(self):
        error_msg = (
            "Last name should be 2 to 20 characters and "
            "can contain dashes, apostrophe, periods and comma"
        )
        names = ["a", "a" * 21, "a0", "a_"]
        for name in names:
            errors = TaggUser.objects.is_lastname_valid({"last_name": name})
            self.assertTrue(len(errors) == 1)
            self.assertTrue("last_name" in errors)
            self.assertEqual(errors["last_name"], error_msg)

    def test_valid_birthdays(self):
        birthdays = ["2000-01-01", "2000-1-1", "2000-1-01"]
        for bd in birthdays:
            errors = TaggUser.objects.is_birthday_valid({"birthday": bd})
            self.assertTrue(len(errors) == 0)

    def test_invalid_birthday_formats(self):
        error_msg = "Date field formatted incorrectly, should be YYYY-MM-DD"
        birthdays = ["", "foo", "20000101", "January 1, 2000"]
        for bd in birthdays:
            errors = TaggUser.objects.is_birthday_valid({"birthday": bd})
            self.assertTrue(len(errors) == 1)
            self.assertTrue("birthday" in errors)
            self.assertEqual(errors["birthday"], error_msg)

    def test_invalid_birthday_formats2(self):
        error_msg = "Something's not right with your birthday"
        birthdays = ["0000-0-0", "0000-00-00", "2000-13-01"]
        for bd in birthdays:
            errors = TaggUser.objects.is_birthday_valid({"birthday": bd})
            self.assertTrue(len(errors) == 1)
            self.assertTrue("birthday" in errors)
            self.assertEqual(errors["birthday"], error_msg)

    def test_valid_biography(self):
        text = "Hello, John Doe here!"
        errors = TaggUser.objects.is_biography_valid({"biography": text})
        self.assertTrue(len(errors) == 0)

    def test_invalid_biography_length(self):
        text = "a" * 151
        error_msg = "Biography must be no longer than 150 characters"
        errors = TaggUser.objects.is_biography_valid({"biography": text})
        self.assertTrue(len(errors) == 1)
        self.assertTrue("biography" in errors)
        self.assertEqual(errors["biography"], error_msg)

    def test_valid_websites(self):
        websites = [
            "",
            "https://foo.com",
            "http://foo.com",
            "www.foo.com",
            "foo.com",
            "foo.org",
        ]
        for website in websites:
            errors = TaggUser.objects.is_website_valid({"website": website})
            self.assertTrue(len(errors) == 0)

    def test_invalid_websites(self):
        websites = [f'https://{"foo" * 100}.com', "foo"]
        error_msg = "Website formatted incorrectly"
        for website in websites:
            errors = TaggUser.objects.is_website_valid({"website": website})
            self.assertTrue(len(errors) == 1)
            self.assertTrue("website" in errors)
            self.assertEqual(errors["website"], error_msg)

    def test_valid_genders(self):
        genders = ["male", "female", "a" * 20, ""]
        for gender in genders:
            errors = TaggUser.objects.is_gender_valid({"gender": gender})
            self.assertTrue(len(errors) == 0)

    def test_invalid_genders(self):
        genders = ["a" * 21]
        error_msg = "Gender must be no longer than 20 characters"
        for gender in genders:
            errors = TaggUser.objects.is_gender_valid({"gender": gender})
            self.assertTrue(len(errors) == 1)
            self.assertTrue("gender" in errors)
            self.assertEquals(errors["gender"], error_msg)
