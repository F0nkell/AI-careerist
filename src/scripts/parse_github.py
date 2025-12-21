import os
import re
import asyncio
from pathlib import Path
from src.database import AsyncSessionLocal
from src.models.question import Question

DATASETS_DIR = Path("datasets")

async def parse_all_repos():
    print(f"--- STARTING AGGRESSIVE PARSER ---")
    
    if not DATASETS_DIR.exists():
        print("CRITICAL: Datasets directory not found!")
        return

    questions_buffer = []
    files_processed = 0
    debug_printed = False # Чтобы вывести пример только один раз
    
    for root, dirs, files in os.walk(DATASETS_DIR):
        rel_path = os.path.relpath(root, DATASETS_DIR).lower().replace("\\", "/")
        
        # Определение категории
        category = "general"
        if "python" in rel_path: category = "python"
        elif "javascript" in rel_path or "front" in rel_path: category = "frontend"
        elif "java" in rel_path: category = "java"
        elif "hr" in rel_path or "behavior" in rel_path: category = "hr"
        elif "product" in rel_path: category = "product_manager"
        elif "sql" in rel_path: category = "sql"

        for file in files:
            if file.endswith(".md") and "readme" not in file.lower():
                file_path = Path(root) / file
                files_processed += 1
                
                try:
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                    
                    # DEBUG: Показываем начало первого файла, чтобы понять формат
                    if not debug_printed and len(content) > 0:
                        print(f"\n[DEBUG] Content sample from {file}:")
                        print(content[:300])
                        print("-" * 20 + "\n")
                        debug_printed = True

                    local_questions = []

                    # --- СТРАТЕГИЯ 1: HTML SPOILERS (<summary>) ---
                    # Часто используется в tech-interview-handbook
                    if "<summary>" in content:
                        matches = re.findall(r'<summary>(.*?)</summary>(.*?)</details>', content, re.DOTALL)
                        for q, a in matches:
                            local_questions.append((q.strip(), a.strip()))

                    # --- СТРАТЕГИЯ 2: MARKDOWN HEADERS (#, ##) ---
                    # Используется в Hexlet
                    elif "#" in content:
                        blocks = re.split(r'(^|\n)#{1,5}\s+', content)
                        for i in range(1, len(blocks), 2):
                            if i + 1 >= len(blocks): break
                            q = blocks[i].strip().split('\n')[0]
                            a = blocks[i+1].strip()
                            local_questions.append((q, a))

                    # Сохраняем найденное
                    for q_text, a_text in local_questions:
                        # Чистка
                        q_text = re.sub(r'<[^>]+>', '', q_text).strip() # Убрать HTML теги из вопроса
                        if len(q_text) < 5 or len(a_text) < 5: continue
                        
                        questions_buffer.append(Question(
                            category=category,
                            level="all",
                            text=q_text[:500],
                            expected_answer=a_text[:3000],
                            source=f"GitHub: {rel_path}"
                        ))

                    if local_questions:
                        print(f"  -> {file}: Found {len(local_questions)} questions ({category})")

                except Exception as e:
                    print(f"Error reading {file}: {e}")

    print(f"\n--- SCAN FINISHED ---")
    print(f"Total files: {files_processed}")
    print(f"Total questions extracted: {len(questions_buffer)}")

    if questions_buffer:
        print("Saving to DB...")
        async with AsyncSessionLocal() as session:
            batch_size = 500
            for i in range(0, len(questions_buffer), batch_size):
                batch = questions_buffer[i : i + batch_size]
                session.add_all(batch)
                await session.commit()
                print(f"Saved batch {i} - {i + len(batch)}")
        print("SUCCESS.")
    else:
        print("STILL NOTHING found. Please copy the [DEBUG] content above and show me.")

if __name__ == "__main__":
    asyncio.run(parse_all_repos())