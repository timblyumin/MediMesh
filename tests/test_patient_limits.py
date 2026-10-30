import unittest

from pydantic import ValidationError
from app.schemas import PatientCreate


class TestPatientLimits(unittest.TestCase):
    def setUp(self):
        self.patient_data = {
            "name": "Alice Smith", "age": 25,
            "department": "ER", "acuity_level": 3
        }

    def test_accepts_valid_ages(self):
        for age in (0, 25, 120):
            with self.subTest(age=age):
                self.patient_data["age"] = age
                patient = PatientCreate(**self.patient_data)
                self.assertEqual(patient.age, age)

    def test_rejects_out_of_range_ages(self):
        for age in (-1, 121):
            with self.subTest(age=age):
                self.patient_data["age"] = age
                with self.assertRaises(ValidationError):
                    PatientCreate(**self.patient_data)

    def test_accepts_valid_acuity_levels(self):
        for acuity in (1, 3, 5):
            with self.subTest(acuity=acuity):
                self.patient_data["acuity_level"] = acuity
                patient = PatientCreate(**self.patient_data)
                self.assertEqual(patient.acuity_level, acuity)

    def test_rejects_out_of_range_acuity_levels(self):
        for acuity in (0, 6):
            with self.subTest(acuity=acuity):
                self.patient_data["acuity_level"] = acuity
                with self.assertRaises(ValidationError):
                    PatientCreate(**self.patient_data)


if __name__ == "__main__":
    unittest.main()
