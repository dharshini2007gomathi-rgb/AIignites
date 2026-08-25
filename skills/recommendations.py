"""
Domain Concept Recommendation Engine for Ayurvedic Competencies.
Provides mapped classical Ayurvedic and clinical concepts for all 10 skill domains,
along with personalized learning paths based on identified skill gaps.
"""
import logging

logger = logging.getLogger('skills')

SKILL_CONCEPTS_MAP = {
    'Ayurveda Knowledge': {
        'overview': 'Core canonical principles, philosophical foundations, and physiological frameworks of Ayurveda.',
        'concepts': [
            'Tridosha Siddhanta (Vata, Pitta, Kapha properties and vitiation signs)',
            'Sapta Dhatu Poshana Nyaya (Metabolic tissue formation and Ojas)',
            'Srotas & Srotodushti types (Atipravritti, Sanga, Siragranthi, Vimargagamana)',
            'Prakriti Assessment (Physical, physiological, and psychological traits)',
            'Shat Kriya Kala (Six clinical stages of disease progression)',
            'Trisutra Ayurveda (Hetu, Linga, and Aushadha)',
            'Ritucharya & Seasonal Dosha Chaya-Prakopa-Prashama rhythms',
        ],
        'resources': [
            'Charaka Samhita Sutrasthana (Chapters 1, 11, 28)',
            'Sushruta Samhita Sutrasthana (Chapters 21, 35)',
            'Ashtanga Hridaya Sutrasthana (Chapters 1, 11-14)',
        ],
    },
    'Clinical Skills': {
        'overview': 'Diagnostic methods, bedside examination, and classical physical assessment.',
        'concepts': [
            'Ashta Sthana Pariksha (Nadi, Mutra, Mala, Jihva, Shabda, Sparsha, Drik, Akriti)',
            'Dashavidha Rogi Pariksha (Tenfold clinical examination protocol)',
            'Nadi Gati Interpretation (Sarpa, Manduka, Hamsa, and mixed Gatis)',
            'Sama vs Nirama status clinical differentiation',
            'Differential diagnosis of Sandhigata Vata, Amavata, and Vatarakta',
            'Fluid thrill and percussion distinction in Udara Roga',
            'Emergency and critical care symptom recognition in classical Ayurveda',
        ],
        'resources': [
            'Yogaratnakara - Ashta Sthana Pariksha',
            'Charaka Samhita Vimanasthana (Chapter 8)',
            'Madhava Nidana with Madhukosha commentary',
        ],
    },
    'Panchakarma': {
        'overview': 'Classical biopurification protocols, preparatory therapies, and post-cleansing regimens.',
        'concepts': [
            'Purva Karma: Snehana protocols and Samyak Snigdha Lakshana',
            'Swedana modalities (Bashpa, Nadi, Patra Pinda, Valuka Sweda)',
            'Vamana Karma (Indications, Antiki Shuddhi, and Kaphanta Lakshana)',
            'Virechana Karma (Pittanta and Kaphanta outcomes, drug selection)',
            'Basti Kalpana (Niruha mixing order: Madhu-Lavana-Sneha-Kalka-Kwatha)',
            'Matra Basti & Anuvasana administration standards',
            'Samsarjana Krama dietary titration (Peya -> Vilepi -> Yusha -> Mamsa Rasa)',
            'Nasya types and Pratimarsha daily protocol',
        ],
        'resources': [
            'Charaka Samhita Siddhisthana',
            'Sushruta Samhita Chikitsasthana (Chapters 31-38)',
            'Practical Guide to Panchakarma - CCRAS Guidelines',
        ],
    },
    'Kayachikitsa': {
        'overview': 'Internal medicine, disease pathogenesis, formulation selection, and systemic treatments.',
        'concepts': [
            'Amavata Chikitsa (Langhana, Swedana, Tikta-Katu Deepana, Vaitarana Basti)',
            'Prameha management (Sthula vs Krisha Chikitsa, Asanadi / Shilajatu protocols)',
            'Grahani Roga therapy (Takra usage, Deepana-Pachana herbs)',
            'Amlapitta & Vidagdha Jeerna treatment (Avipattikar, Kamadudha Rasa)',
            'Hridroga management with Arjuna and cardio-protective Rasayanas',
            'Jwara Chikitsa (Navajwara Langhana -> Pachana -> Kashaya -> Virechana -> Ghrita)',
            'Medoroga Chikitsa (Guru cha Atarpana regimen and Guggulu protocols)',
        ],
        'resources': [
            'Charaka Samhita Chikitsasthana (Chapters 3, 6, 15, 26, 28)',
            'Chakradatta - Kayachikitsa Prakarana',
            'Bhaishajya Ratnavali',
        ],
    },
    'Dravyaguna': {
        'overview': 'Ayurvedic pharmacology, Materia Medica, herbal properties, and pharmacognosy.',
        'concepts': [
            'Rasa Panchaka (Rasa, Guna, Virya, Vipaka, Prabhava evaluation)',
            'Pharmacological actions of core Rasayana herbs (Ashwagandha, Guduchi, Shatavari)',
            'Triphala Churna classical components and 1:1:1 API standardization',
            'Ritu Haritaki Anupana according to six seasonal cycles',
            'Classical Shodhana purification methods for Guggulu and Vatsanabha',
            'Pharmacognostical quality parameters (Acid-Insoluble Ash, Alcohol Extractive)',
            'Phytochemical biomarker quantification (Curcumin, Withaferin-A, Guggulsterones)',
        ],
        'resources': [
            'Dravyaguna Vijnana by Prof. P.V. Sharma',
            'Ayurvedic Pharmacopoeia of India (API - Part I & II)',
            'Bhavaprakasha Nighantu',
        ],
    },
    'Research Methodology': {
        'overview': 'Clinical trial design, biostatistics, evidence-based research, and ethical governance.',
        'concepts': [
            'Reverse Pharmacology paradigm ("Bedside-to-Bench" translational research)',
            'CTRI (Clinical Trials Registry - India) prospective registration mandates',
            'CONSORT guidelines extension for Herbal & Traditional Medicine trials',
            'Good Clinical Practice (GCP) and Institutional Ethics Committee (IEC) governance',
            'Statistical significance interpretation (p-values, 95% Confidence Intervals)',
            'Sample size calculation parameters (Alpha error, Power 1-Beta, Effect size)',
            'Blinding strategies for organoleptically distinct herbal decoctions (Kwathas)',
            'Systematic Review & Meta-Analysis methodology (PRISMA guidelines)',
        ],
        'resources': [
            'ICMR Ethical Guidelines for Biomedical Research',
            'GCP Guidelines for AYUSH Clinical Trials (Ministry of AYUSH)',
            'WHO Guidelines for Methodologies on Research and Evaluation of Traditional Medicine',
        ],
    },
    'Documentation': {
        'overview': 'Clinical case record standards, hospital accreditation, pharmacovigilance, and legal compliance.',
        'concepts': [
            'NABH AYUSH Hospital Accreditation Standards (24-hour initial IPD assessment)',
            'CARE Guidelines (13-item consensus checklist for publishing clinical case reports)',
            'Standard Operating Procedures (SOP) & Batch Manufacturing Records (BMR) for GMP',
            'Informed Consent documentation for specialized procedures (Ksharasutra / Agnikarma)',
            'National AYUSH Pharmacovigilance reporting form for Adverse Drug Reactions (ADR)',
            'Inpatient Discharge Summary standard components and follow-up directives',
            'Statutory medical record retention rules (minimum 3 years for IPD records)',
        ],
        'resources': [
            'NABH Accreditation Standards for AYUSH Hospitals',
            'Drugs & Cosmetics Act 1940 - Schedule T (GMP Guidelines)',
            'CARE Guidelines for Case Reports in Medicine',
        ],
    },
    'Communication': {
        'overview': 'Doctor-patient relationship, dietary compliance counseling, empathetic care, and integrative dialogue.',
        'concepts': [
            'Motivational interviewing for chronic lifestyle & Pathya compliance',
            'Ethical communication in Yapya (incurable but manageable) disorders',
            'Supportive reassurance during Panchakarma Vega emergence',
            'Integrative clinical handovers using the SBAR framework',
            'Swastha Vritta public health communication using intuitive analogies',
            'Teach-Back methodology and pictorial dosing charts for geriatric care',
            'Debunking health misinformation with clinical empathy and classical evidence',
        ],
        'resources': [
            'Charaka Samhita Vimanasthana - Sambhasha Parishad',
            'Clinical Communication Skills in Healthcare',
            'WHO Guidelines on Physician-Patient Communication',
        ],
    },
    'Digital Skills': {
        'overview': 'Health informatics, AYUSH digital ecosystems, telemedicine, and research databases.',
        'concepts': [
            'NAMASTE Portal & WHO ICD-11 Chapter 26 (Traditional Medicine) dual coding',
            'AYUSH Telemedicine Practice Guidelines and statutory digital record keeping',
            'AYUSH Research Portal & DHARA database navigation for evidence synthesis',
            'Ayush Grid national digital health infrastructure and ABHA ID integration',
            'Hospital Information Management Systems (HIMS) & Role-Based Access Control',
            'Digital pulse analysis systems (tactile pressure transducer waveform analysis)',
            'Statistical computing software (SPSS, R, Python) for AYUSH datasets',
            'Reference management software (Zotero, Mendeley) for research publications',
        ],
        'resources': [
            'Ministry of AYUSH - NAMASTE Portal Guide',
            'National Health Authority - Ayushman Bharat Digital Mission (ABDM)',
            'Telemedicine Guidelines for AYUSH Practitioners',
        ],
    },
    'Shalya Tantra': {
        'overview': 'Surgical and para-surgical techniques, wound management, and specialized anorectal procedures.',
        'concepts': [
            'Apamarga Ksharasutra 21-layer preparation (Snuhi latex, Apamarga Kshara, Haridra)',
            'Ksharasutra mechanism of simultaneous cutting and healing in Bhagandara',
            'Vrana Prakshalana decoctions (Triphala / Panchavalkala Kwatha)',
            'Agnikarma thermal micro-cauterization indications for intractable Vata-Kaphaja pain',
            'Jalaukavacharana (Leech therapy) for Pitta-Rakta ulcers and delicate patients',
            'Ashtavidha Shastra Karma (Chedana, Bhedana, Lekhana, Vyadhana, etc.)',
            'Eshani probe usage for fistula tract exploration',
            'Jatyadi Taila & Ghrita applications for Vrana Ropana',
            'Pratisaraneeya Kshara chemical coagulation in internal hemorrhoids (Arsha)',
        ],
        'resources': [
            'Sushruta Samhita Sutrasthana (Chapters 5, 8, 11, 12, 13, 25)',
            'Sushruta Samhita Chikitsasthana (Chapters 1, 2, 6, 8)',
            'Ksharasutra Technique - CCRAS Monograph',
        ],
    },
}


def get_concepts_for_skill(skill_name):
    """Retrieve detailed concept recommendations and resources for a skill."""
    name_cleaned = skill_name.strip()
    data = SKILL_CONCEPTS_MAP.get(name_cleaned)
    if not data:
        for k, v in SKILL_CONCEPTS_MAP.items():
            if k.lower() in name_cleaned.lower() or name_cleaned.lower() in k.lower():
                return v
        return {
            'overview': f'Core domain concepts for {skill_name}.',
            'concepts': [
                f'Foundational theory and classical definitions of {skill_name}',
                f'Clinical application and case studies in {skill_name}',
                f'Diagnostic evaluation methods and modern correlations',
                f'Practical protocols and standard operating procedures',
            ],
            'resources': [
                'Classical Ayurvedic texts (Charaka, Sushruta)',
                'AYUSH Portal learning modules',
            ],
        }
    return data


def generate_personalized_learning_path(student, gap_data=None):
    """
    Generate a personalized learning path roadmap for a student based on:
    - Target CareerPath requirements
    - Current Verified Skill Scores vs Required Benchmarks
    - Identified skill gaps (weak skills)

    Can accept pre-computed gap_data to prevent recursive circular lookups.
    """
    if gap_data is None:
        if not student or not student.career_path:
            return {
                'has_recommendations': False,
                'message': 'Select your target Career Path in your profile to generate a personalized learning roadmap.',
                'prioritized_skills': [],
                'roadmap': [],
            }
        
        career_path = student.career_path
        requirements = career_path.skill_requirements.select_related('skill').all()
        student_skills = {ss.skill_id: float(ss.score) for ss in student.skills.all()}
        is_validated = getattr(student, 'is_skill_validated', False)

        prioritized_gaps = []
        for req in requirements:
            cur = student_skills.get(req.skill_id, 0.0)
            req_score = float(req.required_score)
            gap = max(0.0, req_score - cur)
            if gap > 0:
                prioritized_gaps.append({
                    'skill_id': req.skill_id,
                    'skill_name': req.skill.skill_name,
                    'category': req.skill.category,
                    'current_score': cur,
                    'required_score': req_score,
                    'skill_gap': gap,
                    'priority_level': req.priority_level,
                    'skill_status': 'NEEDS_IMPROVEMENT',
                })
        career_path_dict = {
            'id': career_path.id,
            'name': career_path.name,
            'category': career_path.career_category,
        }
    else:
        career_path_dict = gap_data.get('career_path', {})
        prioritized_gaps = gap_data.get('prioritized_gaps', [])
        is_validated = gap_data.get('is_validated', False)

    if not career_path_dict or not prioritized_gaps:
        return {
            'has_recommendations': bool(career_path_dict),
            'message': 'All career competency benchmarks are met! Continue reviewing advanced clinical cases.' if career_path_dict else 'Select your target Career Path in your profile.',
            'prioritized_skills': [],
            'roadmap': [
                {
                    'step': 1,
                    'phase': 'Phase 1: Foundation',
                    'title': 'Core Competency Review',
                    'action': 'Review fundamental principles across all Ayurvedic clinical domains.',
                    'timeframe': 'Weeks 1-2',
                    'milestone': 'Build strong theoretical baseline',
                },
                {
                    'step': 2,
                    'phase': 'Phase 2: Practice',
                    'title': 'Case Scenario Solving',
                    'action': 'Practice clinical case studies and Chikitsa diagnostic pathways.',
                    'timeframe': 'Weeks 3-4',
                    'milestone': 'Achieve clinical diagnostic fluency',
                },
                {
                    'step': 3,
                    'phase': 'Phase 3: Concept Testing',
                    'title': 'Concept Validation Tests',
                    'action': 'Take regular concept validation tests to verify objective mastery.',
                    'timeframe': 'Weeks 5-6',
                    'milestone': 'Score 80%+ on role-specific tests',
                },
                {
                    'step': 4,
                    'phase': 'Phase 4: Opportunities',
                    'title': 'Opportunity Applications',
                    'action': 'Apply for verified clinical internships and research fellowships.',
                    'timeframe': 'Ongoing',
                    'milestone': 'Secure target clinical placement',
                },
            ],
        }

    # Build prioritized skills list with specific concepts to learn
    prioritized_skills = []
    for gap_item in prioritized_gaps[:5]:
        s_name = gap_item['skill_name']
        cur_score = float(gap_item['current_score'])
        req_score = float(gap_item['required_score'])
        gap_val = float(gap_item['skill_gap'])
        priority = gap_item.get('priority_level', 'Medium')
        
        score_label = "verified score" if is_validated else "self-reported score"
        reason_text = (
            f"Your current {score_label} is {cur_score:.0f}%, while your target career path "
            f"({career_path_dict.get('name', 'Selected Path')}) requires a benchmark of {req_score:.0f}% (Gap: {gap_val:.0f}%)."
        )
        
        concept_info = get_concepts_for_skill(s_name)
        
        prioritized_skills.append({
            'skill_id': gap_item.get('skill_id'),
            'skill_name': s_name,
            'category': gap_item.get('category', 'Core'),
            'current_score': cur_score,
            'required_score': req_score,
            'gap': gap_val,
            'priority': priority,
            'reason': reason_text,
            'concepts_to_learn': concept_info.get('concepts', []),
            'overview': concept_info.get('overview', ''),
        })

    top_skill = prioritized_skills[0]['skill_name'] if prioritized_skills else 'Target Skills'
    roadmap = [
        {
            'step': 1,
            'phase': 'Phase 1: Foundation',
            'title': f'Master Foundational Concepts in {top_skill}',
            'action': f'Study core concepts ({", ".join(prioritized_skills[0]["concepts_to_learn"][:2])}) from canonical Ayurvedic Samhitas.',
            'timeframe': 'Weeks 1-2',
            'milestone': f'Understand fundamentals of {top_skill}',
        },
        {
            'step': 2,
            'phase': 'Phase 2: High-Yield Topics',
            'title': 'Deep-Dive into Critical Clinical Topics',
            'action': 'Study diagnostic criteria, differential diagnosis, and formulation rationales.',
            'timeframe': 'Weeks 3-4',
            'milestone': 'Complete domain reading and clinical notes',
        },
        {
            'step': 3,
            'phase': 'Phase 3: Scenario Practice',
            'title': 'Clinical Vignette & Case Scenario Practice',
            'action': 'Solve objective questions, case vignettes, and diagnostic simulations.',
            'timeframe': 'Weeks 5-6',
            'milestone': 'Achieve 80%+ accuracy in clinical MCQs',
        },
        {
            'step': 4,
            'phase': 'Phase 4: Validation & Mastery',
            'title': 'Retake Concept Validation Test',
            'action': f'Take a fresh concept validation test to boost your verified score to benchmark level.',
            'timeframe': 'Week 7 onwards',
            'milestone': 'Reach Verified Job-Ready status',
        },
    ]

    return {
        'has_recommendations': True,
        'career_path': career_path_dict,
        'prioritized_skills': prioritized_skills,
        'roadmap': roadmap,
    }
