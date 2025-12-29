from Self_Improvement.taskmaster import start_long_term_project
from Self_Improvement.projects import ProjectStore


def main():
    store = ProjectStore()
    cfg = start_long_term_project(
        goal=(
            "إعداد بحث متكامل عن تهريب الأدوية في مأرب وتجهيزه في صورة كتاب مبسّط"
        ),
        horizon_days=30,
        daily_task_budget=2,
        store=store,
    )
    print("✅ تم إنشاء مشروع طويل الأمد")
    print("project_id:", cfg.project_id)
    print("goal:", cfg.goal)


if __name__ == "__main__":
    main()
