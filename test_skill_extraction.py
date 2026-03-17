#!/usr/bin/env python3
"""Test skill extraction on sample text"""

import sys
sys.path.insert(0, 'backend')

from core.skill_extractor import SkillExtractor

# Actual job description from Adzuna
job_text = """
Job Description

We are looking for an AI Engineer to join the Logistics Data & Machine Learning Platform team on our journey to always deliver amazing experiences.

In our Logistics Team, you’ll tackle high-impact challenges that make last-mile delivery efficient, affordable, and sustainable. Your work will directly improve experiences for riders, end customers, and merchants across the globe. Each enhancement you contribute will help Delivery Hero optimize delivery operations, supporting expansion into new areas like grocery and retail.

The Data & ML Platform team’s mission is to enable teams across the organization to build, deploy, and scale intelligent products powered by data and machine learning. As part of this team, you will contribute to the core AI agent platform, helping build infrastructure and services that power production AI applications used across the company.

As an AI Engineer, you will contribute to building scalable systems that support LLM-powered agents, intelligent automation, and data-aware AI services. This role combines AI engineering, backend development, and ML systems, with a strong focus on building reliable systems and learning how to operate AI workloads in production.

In this role you will,

Contribute to building AI agents that interact with internal tools, APIs, and data systems.

Assist in developing and maintaining Retrieval-Augmented Generation (RAG) pipelines using vector databases and semantic retrieval systems.

Support the development of evaluation frameworks and guardrails to improve response quality and reliability of LLM-powered systems.

Help implement monitoring and observability for AI workloads to track performance, usage, and system health.

Collaborate with data scientists, ML engineers, and platform engineers to integrate AI systems into the broader data and ML ecosystem.

Participate in experimenting with new AI frameworks, tools, and approaches to improve the platform
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
