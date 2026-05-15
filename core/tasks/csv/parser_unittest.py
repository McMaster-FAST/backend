import unittest
from parser import parse_questions_from_csv

EXPECTED = [
    {
        'answer': 'C',
        'blooms_tag': 'Rem',
        'comments': '',
        'content': 'In what form is the greatest percentage of carbon dioxide transported in the blood?',
        'descriptor_tag': 'CO2TransportForm',
        'difficulty': 1.0,
        'explanation': "Bloom's Level: Remember | Topic: Respiratory System: CO₂ Transport & Regulation of Ventilation | Subtopic: Carbon Dioxide Transport",
        'images': [],
        'option_explanations': [
            'Incorrect. Only about 7% of CO₂ is transported dissolved in blood plasma. Although CO₂ is more soluble than O₂, the dissolved form still represents a small fraction of total CO₂ transport.',
            'Incorrect. About 23% of CO₂ is transported as carbaminohemoglobin, where CO₂ binds to the protein (globin) portion of hemoglobin. This is the second most common transport method, not the greatest.',
            'Correct. Approximately 70% of CO₂ is transported as bicarbonate ions. Inside red blood cells, carbonic anhydrase catalyzes the reaction of CO₂ with water to form carbonic acid, which quickly dissociates into bicarbonate ions and hydrogen ions. The bicarbonate ions are then shuttled into the plasma.',
            'Incorrect. Oxygen binds to the iron-containing heme groups of hemoglobin, not CO₂. Carbon dioxide binds to the globin (protein) portion of hemoglobin. This is a common point of confusion between O₂ and CO₂ binding sites on hemoglobin.'
        ],
        'options': [
            'Dissolved in blood plasma',
            'Bound to the globin portion of hemoglobin as carbaminohemoglobin',
            'As bicarbonate ions in blood plasma',
            'Bound to the iron portion of hemoglobin'
        ],
        'q_num_tag': 1.0,
        'serial_number': 'WeeklyTest-RespCO2Reg-CO2Trans-CO2TransportForm-Q1-Rem-1',
        'source_tag': 'WeeklyTest',
        'subtopic_tag': 'CO2Trans',
        'unit_tag': 'RespCO2Reg'
    },
    {
        'answer': 'C',
        'blooms_tag': 'Rem',
        'comments': '',
        'content': 'Where does the lingual frenulum attach?',
        'descriptor_tag': 'LingualFrenulumAnat',
        'difficulty': 1.0,
        'explanation': "Bloom's Level: Remember | Topic: Digestive System: Histology, Peritoneum & Mouth | Subtopic: Oral Cavity",
        'images': [],
        'option_explanations': [
            'Incorrect. The uvula hangs from the posterior edge of the soft palate and helps close off the nasopharynx during swallowing. The lingual frenulum is located on the underside of the tongue, not connected to the uvula.',
            'Incorrect. This describes the superior labial frenulum, which connects the upper lip to the gums. The lingual frenulum is located on the underside of the tongue.',
            'Correct. The lingual frenulum is a thin fold of mucous membrane on the underside of the tongue that attaches it to the floor of the oral cavity, limiting excessive posterior tongue movement.',
            'Incorrect. No frenulum connects the hard palate to the pharynx. The lingual frenulum specifically connects the underside of the tongue to the floor of the mouth.'
        ],
        'options': [
            'From the uvula to the soft palate',
            'From the superior lip to the upper gums',
            'From the underside of the tongue to the floor of the mouth',
            'From the hard palate to the posterior pharyngeal wall'
        ],
        'q_num_tag': 1.0,
        'serial_number': 'Vesalian-DigestHistPerMouth-OralCav-LingualFrenulumAnat-Q1-Rem-1',
        'source_tag': 'Vesalian',
        'subtopic_tag': 'OralCav',
        'unit_tag': 'DigestHistPerMouth'
    },
    {
        'answer': 'A',
        'blooms_tag': 'Und',
        'comments': '',
        'content': 'In a patient with emphysema, what is the primary mechanism causing shortness of breath?',
        'descriptor_tag': 'EmphysemaAirTrap',
        'difficulty': 2.0,
        'explanation': "Bloom's Level: Understand | Topic: Respiratory System: Ventilation | Subtopic: Factors Affecting Ventilation",
        'images': [],

        'option_explanations': [
            'Correct. Emphysema destroys the elastic fibers surrounding the alveoli and breaks down alveolar walls. This loss of elastic recoil means the alveoli cannot spring back to their resting size during expiration, trapping air and preventing efficient gas exchange. Normal expiration depends on this elastic recoil as a passive process.',
            'Incorrect. Bronchoconstriction is characteristic of asthma, not emphysema. In emphysema, the primary problem is destruction of alveolar walls and loss of elastic recoil, not airway narrowing at the terminal bronchiole level.',
            'Incorrect. While inhaled irritants (such as cigarette smoke) initiate the damage in emphysema, the resulting pathology is destruction of alveolar walls and loss of elasticity, not accumulation of particles causing collapse. Alveolar collapse (atelectasis) is a separate condition.',
            'Incorrect. Surfactant reduces surface tension, not increases it. In emphysema, the problem is loss of elastic tissue, not changes in surfactant levels. Conditions involving surfactant deficiency (such as neonatal respiratory distress syndrome) are distinct from emphysema.'
        ],
        'options': [
            'Air becomes trapped in the alveoli during expiration due to loss of elastic recoil',
            'The terminal bronchioles constrict and prevent air from reaching the alveoli',
            'Toxic particles accumulate on the alveolar surface and cause the alveoli to collapse',
            'Excess surfactant production increases surface tension within the alveoli'
        ],
        'q_num_tag': 1.0,
        'serial_number': 'Exam-RespVent-FactVent-EmphysemaAirTrap-Q1-Und-2',
        'source_tag': 'Exam',
        'subtopic_tag': 'FactVent',
        'unit_tag': 'RespVent'
    },
    {
        'answer': 'A',
        'blooms_tag': 'Und',
        'comments': '',
        'content': 'What is the primary reason blood velocity is much lower in the capillaries than in the aorta?',
        'descriptor_tag': 'CapVelocityReason',
        'difficulty': 2.0,
        'explanation': "Bloom's Level: Understand | Topic: Blood Vessel: Physiology | Subtopic: Hemodynamics (Flow, Pressure, Resistance)",
        'images': [],
        'option_explanations': [
            'Correct. Although individual capillaries are tiny, the enormous number of them creates a massive total cross-sectional area. Blood velocity is inversely proportional to total cross-sectional area, so the same volume of blood spreads across this large area and moves much more slowly, allowing adequate time for gas and nutrient exchange.',
            'Incorrect. While individual capillaries are smaller in diameter, this alone does not explain the decreased velocity. It is the enormous total cross-sectional area created by millions of capillaries combined that slows blood velocity, not the small size of each individual vessel.',
            'Incorrect. Capillary walls are actually the thinnest of all blood vessels, consisting only of endothelium and a basement membrane. Blood velocity decreases in capillaries primarily because the total cross-sectional area increases dramatically when blood is distributed across millions of vessels.',
            'Incorrect. While pressure does drop by the time blood reaches the capillaries, the primary determinant of blood velocity is the total cross-sectional area of the vascular bed. The massive increase in total cross-sectional area at the capillary level is the main factor reducing velocity.'
        ],
        'options': [
            'The total cross-sectional area of all capillaries combined is far greater than that of the aorta',
            'Individual capillaries have much smaller diameters than the aorta',
            'Capillary walls generate more friction because they are composed of thicker tissue',
            'The pressure gradient across the capillary bed is too small to maintain high velocity'
        ],
        'q_num_tag': 2.0,
        'serial_number': 'BRIDGE-BVPhys-Hemodynamics-CapVelocityReason-Q2-Und-2',
        'source_tag': 'BRIDGE',
        'subtopic_tag': 'Hemodynamics',
        'unit_tag': 'BVPhys'
    }
]
class TestParseQuestions(unittest.TestCase):

    def assertQuestionEqual(self, got, exp, idx):
        # Ensure same keys exist
        self.assertEqual(set(got.keys()), set(exp.keys()), f"Key mismatch at index {idx}")

        # Compare field-by-field for clarity
        for key in exp:
            self.assertEqual(
                got[key],
                exp[key],
                f"Mismatch at index {idx} in field '{key}'"
            )

    def test_parse_questions(self):
        result = list(parse_questions_from_csv("input/TestFile.csv"))

        self.assertEqual(
            len(result),
            len(EXPECTED),
            "Number of questions mismatch"
        )

        for i, (got, exp) in enumerate(zip(result, EXPECTED)):
            self.assertQuestionEqual(got, exp, i)


if __name__ == "__main__":
    unittest.main()