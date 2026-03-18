#!/usr/bin/env python3
"""Test skill extraction on sample text"""

import sys
sys.path.insert(0, 'backend')

from core.skill_extractor import SkillExtractor

# Actual job description from Adzuna
job_text = """
Join KPMG and our clients in their AI transformation. In this role, you will be responsible for operational excellence in the development and implementation of AI solutions in consulting projects through the AI ​​Center of Excellence (CoE). Your role is crucial in embedding our AI strategy within the company and in projects. Through your successful implementations, you will position the CoE as an internal driving force for successful transformation. Want to


use

your expertise to advance our area? Then you can contribute here:

Practical AI solutions: You will support the development of AI solutions that can be directly applied in customer projects. You will learn to use generative AI and modern machine learning techniques.
Technical support: You will work with experienced colleagues to develop a deep understanding of technical architectures. You will assist with implementation and learn to take responsibility for parts of a project.
Collaboration: You will work closely with consultants, data scientists, and client teams. You will learn how to transform innovative AI ideas into scalable applications.
Learn architecture: You will support the design of AI architectures that can be integrated into existing systems, including data flows, security, and governance.
Building prototypes: You contribute your ideas and help in the development of prototypes. You learn how to develop technical decision-making criteria within a project context.
Knowledge transfer: You will assist in creating formats for knowledge transfer and quality assurance in the use of AI. You will learn how to effectively share knowledge in everyday project work.




Your profile

Academic qualification: You have completed a degree in computer science, engineering, or a related field. Prior experience with artificial intelligence, machine learning, or data science is advantageous.
Initial experience: You have already gained initial experience in the conception and implementation of AI systems as well as NLP, machine learning, chatbots or automations.
Programming languages: You are familiar with programming languages ​​such as Python, JavaScript, TypeScript or R and have already worked with AI frameworks.
Enthusiasm for technology: You are curious about new technologies and can assess and classify technical trends well.
Collaboration: You enjoy taking on responsibility and have a good sense for the collaboration between business, tech, and governance.
Language skills: You have excellent oral and written communication skills in German and English to operate confidently in an international environment.


Your benefits

Welcome to the team! To ensure you get off to a great start, we'll support you with structured onboarding measures throughout your orientation phase. Your manager will also actively promote your professional and personal integration into the team.
Diverse career prospects: We value the individual development of your professional and personal strengths. We reflect on your ambitions in structured development discussions. Systematic and regular feedback sessions support you in achieving these goals. With our diverse range of exciting clients and challenges, we offer you interesting career opportunities and valuable insights into the variety of our fields of activity.
Work-Life Balance: We are convinced that diversity and flexibility are essential for fostering innovation and ensuring long-term success. Only in this way can we develop the best ideas and find truly innovative solutions. With flexible working hours, a home office option, time accounts, and sabbaticals, we create opportunities to reconcile your private and professional life. Furthermore, we support you with up to four hours of paid time off per month for your social engagement.
Further training and education: Through regular training sessions, workshops and further education courses, you will continuously develop your skills.
The services shown may vary slightly depending on the position and location.
"""

resume_text = """
Senior Software Engineer with 5 years of experience.
Skills: Python, SQL, Git, GitHub, Google Cloud Run, Docker, Kubernetes
Experience with Agile, Jira, Confluence
Fluent in English and German
"""

extractor = SkillExtractor()

print("=" * 60)
print("JOB DESCRIPTION SKILLS:")
print("=" * 60)
job_skills = extractor.extract_skills(job_text)
print(f"Extracted {len(job_skills)} skills:")
for skill in sorted(job_skills):
    print(f"  - {skill}")

print("\n" + "=" * 60)
print("RESUME SKILLS:")
print("=" * 60)
resume_skills = extractor.extract_skills(resume_text)
print(f"Extracted {len(resume_skills)} skills:")
for skill in sorted(resume_skills):
    print(f"  - {skill}")

print("\n" + "=" * 60)
print("MATCHED SKILLS:")
print("=" * 60)
matched = resume_skills & job_skills
print(f"Found {len(matched)} matches:")
for skill in sorted(matched):
    print(f"  - {skill}")

print("\n" + "=" * 60)
print("MISSING SKILLS (in job but not in resume):")
print("=" * 60)
missing = job_skills - resume_skills
print(f"Found {len(missing)} missing:")
for skill in sorted(missing):
    print(f"  - {skill}")
