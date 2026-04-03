#!/bin/bash

echo "🚀 Creating Resume AI Project Structure..."

# Root folder
mkdir -p resume-ai
cd resume-ai

# Backend structure
mkdir -p backend/app/routes
mkdir -p backend/app/services
mkdir -p backend/app/utils
mkdir -p backend/app/models

# Frontend
mkdir -p frontend/components

# Notebook
mkdir -p notebooks

# Create files
touch backend/app/main.py
touch backend/app/config.py

touch backend/app/routes/resume.py
touch backend/app/routes/github.py

touch backend/app/services/llm_service.py
touch backend/app/services/pinecone_service.py
touch backend/app/services/parser_service.py
touch backend/app/services/github_service.py
touch backend/app/services/resume_builder.py

touch backend/app/utils/embedding.py
touch backend/app/utils/helpers.py

touch backend/app/models/request_models.py
touch backend/app/models/response_models.py

touch backend/requirements.txt
touch backend/.env

touch frontend/app.py
touch notebooks/trials.ipynb


echo "✅ Project structure created successfully!"