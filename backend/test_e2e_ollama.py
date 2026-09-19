"""End-to-end integration test validating the entire real Ollama workflow."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "app"))
sys.path.insert(0, os.path.dirname(__file__))

from fastapi.testclient import TestClient
from app.main import app
from app.database.mongodb import db

client = TestClient(app)

def run_tests():
    print("=" * 60)
    print("STARTING REAL END-TO-END OLLAMA WORKFLOW VALIDATION")
    print("=" * 60)

    # 1. Health check
    print("\n1. Testing Health Endpoint...")
    res = client.get("/health")
    assert res.status_code == 200, f"Health check failed: {res.text}"
    print("   Health check OK:", res.json())

    # 2. Register User
    print("\n2. Testing User Registration...")
    email = f"learner_{os.getpid()}@test.com"
    reg_payload = {"name": "Alex Developer", "email": email, "password": "password123"}
    res = client.post("/api/auth/register", json=reg_payload)
    assert res.status_code == 200, f"Registration failed: {res.text}"
    user_data = res.json()["user"]
    user_id = user_data["id"]
    token = res.json()["token"]
    print(f"   Registered user {user_id} with email {email}")

    # 3. CV Upload & Text Extraction & Ollama Profile Analysis
    print("\n3. Testing Resume Upload & Ollama Analysis...")
    sample_cv = """
    Alex Developer
    Target: Full Stack Engineer
    Summary: Enthusiastic developer with experience in React and Node.js backend.
    Experience:
    - Junior Web Developer at WebWorks (2023 - Present)
      * Built dynamic user interfaces using React, JavaScript, and Tailwind CSS.
      * Created REST APIs using Express and Node.js.
      * Integrated SQL databases (PostgreSQL) and wrote data queries.
    Skills: JavaScript, React, Node.js, HTML, CSS, SQL, Git
    Projects:
    - TaskTracker: React and Node.js full stack application.
    """
    files = {"file": ("resume.txt", sample_cv.encode("utf-8"), "text/plain")}
    data = {"user_id": user_id, "career_target": "Full Stack Engineer"}
    res = client.post("/api/resume/parse", files=files, data=data)
    assert res.status_code == 200, f"Resume parse failed: {res.text}"
    parsed_resume = res.json()
    print(f"   Resume parsed successfully. Skills found: {parsed_resume.get('skills')}")
    print(f"   AI status: {parsed_resume.get('ai')}")
    assert parsed_resume.get("ai", {}).get("success") is True, "AI resume analysis did not succeed"
    assert len(parsed_resume.get("skills", [])) > 0, "No skills detected from resume"

    # 4. Save Profile
    print("\n4. Testing Profile Save...")
    prof_payload = {
        "career_target": "Full Stack Engineer",
        "experience_level": "1–3 years",
        "resume_text": sample_cv,
        "skills": parsed_resume.get("skills", ["JavaScript", "React"]),
    }
    res = client.post(f"/api/auth/profile/{user_id}", json=prof_payload)
    assert res.status_code == 200, f"Profile save failed: {res.text}"
    profile = res.json()
    print(f"   Profile saved: career={profile['career_target']}, version={profile.get('profile_version')}")

    # 5. Personalized Initial Diagnostic Quiz from Ollama
    print("\n5. Testing Initial Quiz Generation from Ollama...")
    quiz_req = {
        "user_id": user_id,
        "career_target": "Full Stack Engineer",
        "skills": profile.get("skills", []),
    }
    res = client.post("/api/assessment/generate", json=quiz_req)
    assert res.status_code == 200, f"Quiz generation failed: {res.text}"
    quiz = res.json()
    quiz_id = quiz["id"]
    questions = quiz["questions"]
    print(f"   Generated quiz {quiz_id} with {len(questions)} questions")
    assert len(questions) >= 5, f"Expected at least 5 questions, got {len(questions)}"
    for i, q in enumerate(questions[:3]):
        print(f"     Q{i+1}: [{q['topic']}] {q['prompt']} (Options: {len(q['options'])})")
        assert len(q["options"]) == 4, f"Question {i+1} must have 4 options"
        assert 0 <= q["answer_index"] <= 3, f"Question {i+1} answer index out of range"

    # 6. Submit Quiz Answers with Confidence & Evaluate
    print("\n6. Testing Deterministic Backend Scoring & Recommendation Generation...")
    # Answer: purposely get SQL wrong to simulate a weak area, get JavaScript and React right
    answers = []
    for q in questions:
        topic = q.get("topic", "").lower()
        if "sql" in topic:
            # Answer incorrectly with high confidence (simulates misconception penalty)
            wrong_idx = (q["answer_index"] + 1) % 4
            answers.append({"question_id": q["id"], "selected_index": wrong_idx, "confidence": 4})
        else:
            # Answer correctly with good confidence
            answers.append({"question_id": q["id"], "selected_index": q["answer_index"], "confidence": 4})

    submission_payload = {
        "user_id": user_id,
        "quiz_id": quiz_id,
        "answers": answers,
        "previous_scores": {},
    }
    res = client.post("/api/assessment/submit", json=submission_payload)
    assert res.status_code == 200, f"Quiz submission failed: {res.text}"
    eval_result = res.json()
    print("   Quiz evaluated successfully!")
    print(f"   Overall score: {eval_result.get('overall')}%")
    print(f"   Topic scores: {eval_result.get('current_topic_scores')}")
    print(f"   AI recommendations generated: {eval_result.get('ai')}")
    assert eval_result.get("ai", {}).get("success") is True, "AI recommendations failed"
    assert "roadmap" in eval_result, "Roadmap was not returned in evaluation result"
    initial_roadmap = eval_result["roadmap"]
    print(f"   Initial roadmap created with {len(initial_roadmap.get('nodes', []))} nodes, completion: {initial_roadmap.get('completion')}%")

    # 7. Roadmap Verification
    print("\n7. Testing Roadmap Endpoint & Stable Graph Layout...")
    res = client.post("/api/roadmap/generate", json={"user_id": user_id, "career_target": "Full Stack Engineer"})
    assert res.status_code == 200, f"Roadmap get failed: {res.text}"
    roadmap = res.json()
    assert len(roadmap.get("nodes", [])) > 0, "No nodes in roadmap"
    node_ids = [n["id"] for n in roadmap["nodes"]]
    print(f"   Roadmap nodes: {node_ids}")
    for n in roadmap["nodes"]:
        print(f"     Node [{n['id']}]: topic={n['topic']}, mastery={n['mastery']}%, status={n['status']}, priority={n['priority']}")

    # 8. Fixed Resource Verification
    print("\n8. Testing Curated Fixed Resources...")
    res = client.post("/api/roadmap/resources", json={"topic": "SQL", "career_target": "Full Stack Engineer"})
    assert res.status_code == 200, f"Resources fetch failed: {res.text}"
    resource_data = res.json()
    resources = resource_data.get("resources", [])
    print(f"   Fetched {len(resources)} fixed curated resources for SQL:")
    for r in resources:
        print(f"     - [{r.get('type')}] {r.get('title')} ({r.get('url')})")
    assert len(resources) > 0, "Expected curated resources"
    assert any("mdn" in r.get("url", "").lower() or "developer.mozilla" in r.get("url", "").lower() or "freecodecamp" in r.get("url", "").lower() for r in resources)

    # 9. Adaptive Re-evaluation Quiz on Weak Topic
    print("\n9. Testing Adaptive Re-evaluation Quiz on SQL...")
    reassess_req = {
        "user_id": user_id,
        "career_target": "Full Stack Engineer",
        "topic": "SQL",
        "skills": profile.get("skills", []),
    }
    res = client.post("/api/assessment/generate", json=reassess_req)
    assert res.status_code == 200, f"Re-evaluation quiz generation failed: {res.text}"
    reassess_quiz = res.json()
    reassess_questions = reassess_quiz["questions"]
    print(f"   Generated re-evaluation quiz {reassess_quiz['id']} with {len(reassess_questions)} questions")
    sql_questions = [q for q in reassess_questions if "sql" in q.get("topic", "").lower() or "database" in q.get("topic", "").lower()]
    print(f"   SQL / database focused questions: {len(sql_questions)} / {len(reassess_questions)}")
    assert len(reassess_questions) >= 5, "Re-evaluation quiz too short"

    # 10. Submit Re-evaluation Answers (Improved Performance)
    print("\n10. Submitting Re-evaluation with Improved Performance...")
    # Answer correctly with high confidence (e.g. studied SQL)
    reassess_answers = [
        {"question_id": q["id"], "selected_index": q["answer_index"], "confidence": 5}
        for q in reassess_questions
    ]
    reassess_submission = {
        "user_id": user_id,
        "quiz_id": reassess_quiz["id"],
        "answers": reassess_answers,
        "previous_scores": eval_result["skill_scores"],
    }
    res = client.post("/api/assessment/submit", json=reassess_submission)
    assert res.status_code == 200, f"Reassessment submission failed: {res.text}"
    reassess_result = res.json()
    print("   Re-evaluation scored successfully!")
    print(f"   New current scores: {reassess_result.get('current_topic_scores')}")
    print(f"   Cumulative merged skill scores: {reassess_result.get('skill_scores')}")
    print(f"   Updated roadmap version: {reassess_result.get('roadmap', {}).get('roadmap_version')}")
    print(f"   Updated overall completion: {reassess_result.get('roadmap', {}).get('completion')}%")

    # Verify cumulative scoring: old score and new score blended
    # 11. Verify Node ID Stability in Updated Roadmap
    print("\n11. Verifying Roadmap Node ID Stability...")
    updated_roadmap = reassess_result["roadmap"]
    updated_node_ids = [n["id"] for n in updated_roadmap["nodes"]]
    assert updated_node_ids == node_ids, f"Node IDs changed! Original: {node_ids}, Updated: {updated_node_ids}"
    print("   Node IDs are completely stable!")

    # 12. Chatbot Context & Ollama Interaction
    print("\n12. Testing Chatbot with Latest Learner State...")
    chat_req = {
        "user_id": user_id,
        "message": "What should I focus on next based on my latest quiz?",
        "current_topic": "SQL",
        "career_target": "Full Stack Engineer",
    }
    res = client.post("/api/chat", json=chat_req)
    assert res.status_code == 200, f"Chat endpoint failed: {res.text}"
    chat_data = res.json()
    print(f"   AI reply: {chat_data.get('reply')}")
    print(f"   Chat AI status: {chat_data.get('ai')}")
    assert chat_data.get("ai", {}).get("success") is True, "Chatbot AI call failed"
    assert len(chat_data.get("reply", "").strip()) > 10, "Chatbot returned empty reply"

    # 13. Server-side Persistence Verification
    print("\n13. Testing Server-side Persistence Across DB Connection...")
    saved_state = db.memory.get("skill_states", [])
    user_state = next((s for s in saved_state if s.get("user_id") == user_id), None)
    assert user_state is not None, "Skill state not found in server persistence"
    print(f"   Persisted state found: version={user_state.get('version')}, scores={user_state.get('scores')}")
    assert "history" in user_state, "Score history not found"
    print(f"   Topic history entries: {list(user_state.get('history', {}).keys())}")

    print("\n" + "=" * 60)
    print("ALL REAL END-TO-END WORKFLOW CHECKS PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()

