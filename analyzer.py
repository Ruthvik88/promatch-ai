import spacy
from sentence_transformers import SentenceTransformer, util

# Load models once to save time
nlp = spacy.load("en_core_web_md")
model = SentenceTransformer('all-MiniLM-L6-v2')

def extract_keywords(text):
    """
    Extracts key phrases (potential skills) from text using NLP chunks.
    """
    doc = nlp(text)
    # Filter for Noun Chunks and Entities to catch skills like "Python", "Project Management"
    keywords = [chunk.text.strip().lower() for chunk in doc.noun_chunks]
    entities = [ent.text.strip().lower() for ent in doc.ents]
    
    # Combine and deduplicate
    all_terms = list(set(keywords + entities))
    
    # Clean up (remove very short words or stop words)
    cleaned_terms = [term for term in all_terms if len(term) > 2 and term not in nlp.Defaults.stop_words]
    return cleaned_terms

def analyze_resume(resume_text, job_desc_text, threshold=0.5):
    """
    Compares Resume vs Job Description semantically.
    Returns match score, present skills, and missing skills.
    """
    # 1. Extract potential required skills from the Job Description
    job_skills_raw = extract_keywords(job_desc_text)
    
    # 2. Extract content from Resume
    resume_content_raw = extract_keywords(resume_text)
    
    if not job_skills_raw or not resume_content_raw:
        return 0, [], job_skills_raw

    # 3. Create Embeddings
    job_embeddings = model.encode(job_skills_raw, convert_to_tensor=True)
    resume_embeddings = model.encode(resume_content_raw, convert_to_tensor=True)

    # 4. Semantic Search
    # For every job skill, find the best match in the resume
    hits = util.semantic_search(job_embeddings, resume_embeddings, top_k=1)

    present_skills = []
    missing_skills = []

    for i, hit in enumerate(hits):
        job_skill = job_skills_raw[i]
        
        # Check if the best match score is above threshold
        if hit and hit[0]['score'] >= threshold:
            present_skills.append(job_skill)
        else:
            missing_skills.append(job_skill)

    # 5. Calculate Score (Simple Accuracy)
    if len(job_skills_raw) > 0:
        match_score = (len(present_skills) / len(job_skills_raw)) * 100
    else:
        match_score = 0

    return round(match_score, 1), present_skills, missing_skills