# ================================
# models.py
# ================================

from pydantic import BaseModel
from typing import Optional, List


class ReferenceRange(BaseModel):

    min: Optional[str] = None
    max: Optional[str] = None
    text: Optional[str] = None


class Parameter(BaseModel):

    parameter_name: Optional[str] = None
    value: Optional[str] = None
    unit: Optional[str] = None
    reference_range: ReferenceRange
    flag: Optional[str] = None


class PatientInfo(BaseModel):

    name: Optional[str] = None
    age: Optional[str] = None
    gender: Optional[str] = None
    report_date: Optional[str] = None


class TestInfo(BaseModel):

    test_type: Optional[str] = None
    test_name: Optional[str] = None
    category: Optional[str] = None


class Interpretation(BaseModel):

    impression: Optional[str] = None
    summary: Optional[str] = None


class Diagnosis(BaseModel):

    conditions: List[str] = []
    clinical_notes: Optional[str] = None


class Recommendations(BaseModel):

    next_steps: Optional[str] = None
    follow_up: Optional[str] = None
    lifestyle_advice: Optional[str] = None


class LabDetails(BaseModel):

    lab_name: Optional[str] = None
    hospital_name: Optional[str] = None
    doctor_name: Optional[str] = None
    accreditation: Optional[str] = None
    signature_present: Optional[bool] = None


class Metadata(BaseModel):

    report_id: Optional[str] = None
    source: Optional[str] = None
    extraction_confidence: Optional[float] = None


class StructuredReport(BaseModel):

    patient_info: PatientInfo
    test_info: TestInfo
    parameters: List[Parameter]
    interpretation: Interpretation
    diagnosis: Diagnosis
    recommendations: Recommendations
    lab_details: LabDetails
    metadata: Metadata