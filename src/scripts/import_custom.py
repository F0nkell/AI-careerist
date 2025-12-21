import json
import os
import asyncio
from pathlib import Path
from src.database import AsyncSessionLocal
from src.models.question import Question

# Путь внутри контейнера, куда мы скопируем файлы
CUSTOM_DATA_DIR = Path("datasets/custom")

async def import_custom_data():
    if not CUSTOM_DATA_DIR.exists():
        print(f"Directory {CUSTOM_DATA_DIR} not found inside container.")
        return

    async with AsyncSessionLocal() as session:
        # Ищем все .json файлы
        files = list(CUSTOM_DATA_DIR.glob("*.json"))
        if not files:
            print("No .json files found in datasets/custom!")
            return

        total_imported = 0
        
        for file_path in files:
            # Имя файла = Категория (например, marketing.json -> marketing)
            category_name = file_path.stem.lower()
            print(f"Processing category: {category_name}...")
            
            try:
                content = file_path.read_text(encoding="utf-8")
                data = json.loads(content)
                
                count = 0
                for item in data:
                    # Проверка на дубликаты (опционально, но полезно)
                    # Пока просто льем всё
                    q = Question(
                        category=category_name,
                        level=item.get("level", "all"),
                        text=item.get("question"),
                        expected_answer=item.get("answer", ""),
                        source="Custom JSON"
                    )
                    session.add(q)
                    count += 1
                
                await session.commit()
                print(f"-> Imported {count} questions for {category_name}.")
                total_imported += count
                
            except Exception as e:
                print(f"Error parsing {file_path}: {e}")
        
        print(f"DONE! Total questions imported: {total_imported}")

if __name__ == "__main__":
    asyncio.run(import_custom_data())