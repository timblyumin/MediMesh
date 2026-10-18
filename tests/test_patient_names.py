import unittest

from pydantic import ValidationError

from app.schemas import PatientCreate


class TestPatientNames(unittest.TestCase):
    def make_patient(self, name):
        return PatientCreate(
            name=name, age=25, department="ER", acuity_level=2
        )

    def test_trims_surrounding_whitespace(self):
        patient = self.make_patient("  Alice Smith \t")
        self.assertEqual(patient.name, "Alice Smith")

    def test_preserves_internal_spaces(self):
        self.assertEqual(self.make_patient("Alice Smith").name, "Alice Smith")

    def test_rejects_blank_names(self):
        for name in ("", "   ", "\t\n"):
            with self.subTest(name=name):
                with self.assertRaises(ValidationError):
                    self.make_patient(name)

    def test_still_requires_capitalization(self):
        for name in ("alice", "  alice  "):
            with self.subTest(name=name):
                with self.assertRaises(ValidationError):
                    self.make_patient(name)

    def test_length_limit_applies_after_trimming(self):
        name = "A" * 100
        self.assertEqual(self.make_patient(" " + name + " ").name, name)
        with self.assertRaises(ValidationError):
            self.make_patient("A" * 101)

    def test_rejects_non_string_names(self):
        for name in (None, 123):
            with self.subTest(name=name):
                with self.assertRaises(ValidationError):
                    self.make_patient(name)


if __name__ == "__main__":
    unittest.main()
