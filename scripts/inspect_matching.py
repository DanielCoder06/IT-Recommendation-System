import argparse
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]

from src.services.matching.matching_service import recommend_jobs_for_cv, CVContentError

def main(pdf_path: str):
    print(">>> Đang phân tích CV: ")
    try:
        results = recommend_jobs_for_cv(pdf_path, exclude_senior=True, top_k=10, return_details=True)
    except CVContentError as e:
        print(">>> CV Lỗi")
        return

    if not results:
        print(">>> Không có công việc phù hợp")
        return

    print(f">>> Top {len(results)} phù hợp nhất: ")
    print("=" * 100)
    for job in results:
        print(f"#{job['rank']:02d} | {job['title']} @ {job['company']}")
        print(f"     📍 {job['location']} | 💼 {job['experience']}")
        print(f"     🔗 {job['url']}")
        print(f"     ⭐ Match Score: {job['_score']:.4f}")
        print(">>> Chi tiết: ")
        top_matches = job["_details"][:3]
        for match in top_matches:
            sim_percent = match["similarity"] * 100
            
            # Cắt ngắn văn bản để dễ nhìn trên terminal
            jd_preview = match["jd_text"].replace("\n", " ")
            cv_preview = match["cv_text"].replace("\n", " ")
            
            print(f"       [Độ tương đồng: {sim_percent:.1f}%]")
            print(f"       [JD yêu cầu] | {jd_preview}")
            print(f"       [CV đáp ứng] | {cv_preview}")
            print("-" * 100)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf_path", type=str, help="Đường dẫn file CV PDF")
    args = parser.parse_args()
    main(args.pdf_path)