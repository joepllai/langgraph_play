# FHIR-Agent Backend Proof of Concept

This repository is a proof of concept (POC) for building a FHIR-agent backend. It enables users to interact with a chatbot that has the capability to query real healthcare data using FHIR (Fast Healthcare Interoperability Resources).

## Getting Started

# prerequist
    - make sure you provide credential for .env file. you can ref to .env.example to know what env variable you should set


To run the application locally, use the following command:

```bash
uv run -- uvicorn app.main:app --reload
