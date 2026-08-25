# 🌿 AIignites – AI-Powered Career & Skill Assessment Platform for Ayurveda Students

AIignites is an **AI-powered career guidance and skill assessment platform designed specifically for Ayurveda students and graduates**. The platform helps users build professional profiles, assess their skills based on their target roles, identify skill gaps, and receive personalized recommendations for career development.

## 🎯 Problem Statement

Ayurveda students often have limited access to career guidance that is specifically aligned with their field. Existing job platforms mainly provide general job listings and do not deeply evaluate whether a candidate possesses the required skills and concepts for Ayurveda-related roles.

AIignites addresses this gap by combining **career profiling, role-based assessments, skill-gap analysis, and personalized learning recommendations** in one platform.

## 💡 Key Features

### 👤 Profile & Career Assessment

* Create and update a professional profile.
* Add education, skills, certifications, experience, and career interests.
* Perform self-assessment to understand current capabilities.

### 🧠 Role-Based AI Assessment

* Select or search for a target job/internship role.
* Generate assessments based on the selected role.
* Evaluate knowledge, skills, and concepts relevant to that role.
* Provide performance scores and detailed feedback.

### 📊 Skill Gap Analysis

* Compare the user's existing skills with the requirements of the selected role.
* Identify missing or weak skills.
* Highlight areas that need improvement.

### 📚 Personalized Skill Recommendations

After assessment, AIignites recommends:

* Skills to learn
* Concepts to strengthen
* Relevant learning areas
* Areas for practical improvement

### 💼 Career & Internship Support

* Explore suitable career paths.
* Find opportunities relevant to the user's profile.
* Understand the skills expected for different roles.

### 📈 Progress Tracking

* Track assessment performance.
* Monitor skill development.
* Identify improvement areas over time.

## 🔄 System Workflow

```text
User Registration
       ↓
Create / Update Profile
       ↓
Self Assessment
       ↓
Select Target Role
       ↓
Role-Based Assessment
       ↓
Skill & Concept Evaluation
       ↓
Skill Gap Analysis
       ↓
Personalized Recommendations
       ↓
Learning & Skill Development
       ↓
Career / Internship Opportunities
```

## 🛠️ Technology Stack

| Component       | Technology                       |
| --------------- | -------------------------------- |
| Frontend        | HTML, CSS, JavaScript            |
| Backend         | Python, Django                   |
| Database        | SQLite                           |
| AI/Assessment   | AI-based role and skill analysis |
| Styling         | HTML/CSS                         |
| Version Control | Git & GitHub                     |

## 📂 Project Structure

```text
AIignites/
│
├── courses/
├── opportunities/
├── portal/
├── skills/
├── students/
├── static/
├── templates/
├── logs/
│
├── manage.py
├── requirements.txt
├── README.md
└── .gitignore
```

## 🚀 Installation & Setup

### 1. Clone the repository

```bash
git clone https://github.com/dharshini2007gomathi-rgb/AIignites.git
cd AIignites
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate the virtual environment

**Windows:**

```bash
venv\Scripts\activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Run database migrations

```bash
python manage.py migrate
```

### 6. Start the development server

```bash
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```

## 🔐 Security

Sensitive information such as environment variables, local databases, virtual environments, and Python cache files should not be committed to GitHub.

These files are excluded using `.gitignore`.

## 🌟 Project Uniqueness

Unlike general career and job platforms, AIignites focuses specifically on **Ayurveda students and their career requirements**.

The platform goes beyond simply recommending jobs by:

1. **Understanding the user's target role**
2. **Conducting role-specific assessments**
3. **Identifying individual skill gaps**
4. **Recommending skills and concepts to improve**

This creates a continuous **Assess → Analyze → Learn → Improve → Apply** career development cycle.

## 👥 Team Members

* **Dhivya Dharshini S**
* **Dharshini T**
* **Ananth S**
* **Anithan I**
* **Gokul Sri M**
* **Gobika R**

## 🔮 Future Enhancements

* AI-powered resume analysis
* Advanced personalized learning paths
* Interview preparation and mock interviews
* Voice-based AI career mentor
* More Ayurveda-specific job roles and skill datasets
* Multilingual support
* Advanced analytics dashboard
* Integration with external internship and job platforms

## 👩‍💻 Project

**AIignites – AI-Powered Career & Skill Assessment Platform for Ayurveda Students**

### GitHub Repository

https://github.com/dharshini2007gomathi-rgb/AIignites
