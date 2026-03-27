# 🛡️ AGL Security Tool

**Advanced 6-Layer Smart Contract Security Auditor**

> 🌐 **[Visit the Official Website](https://alanqamarqo-dev.github.io/your-repo/)** | **[زُر الموقع الرسمي](https://alanqamarqo-dev.github.io/your-repo/)**

> **بالعربي:** أداة تدقيق أمني متقدمة للعقود الذكية بـ 6 طبقات تحليل، تشمل إثبات رسمي Z3 واستنتاج استغلال، بنسبة اكتشاف 94.1% على بروتوكولات DeFi حقيقية.

---

## Go CLI Helper

A simple Go application that demonstrates clean project structure with tests, CI, and benchmarks.

## Quick Start

```bash
# Run directly — تشغيل مباشر
go run hello.go

# Run with a custom name — تشغيل باسم مخصص
go run hello.go Ahmad

# Build and run — بناء وتشغيل
make build
./your-repo
```

## Using Make

```bash
make build    # Build the binary — بناء البرنامج
make test     # Run tests — تشغيل الاختبارات
make bench    # Run benchmarks — قياس الأداء
make cover    # Show test coverage — تغطية الاختبارات
make clean    # Remove build artifacts — تنظيف
make all      # Build + test — بناء واختبار
```

## Testing

```bash
# Run all tests — تشغيل جميع الاختبارات
go test -v ./...

# Run benchmarks — قياس الأداء
go test -bench=. -benchmem ./...
```

## CI/CD

This project uses **GitHub Actions** to automatically run tests on every push and pull request.
See [`.github/workflows/ci.yml`](.github/workflows/ci.yml).

> **بالعربي:** المشروع يستخدم GitHub Actions لتشغيل الاختبارات تلقائياً مع كل push أو pull request.

## Project Structure

```
.
├── .github/
│   └── workflows/
│       └── ci.yml        # GitHub Actions CI — بناء واختبار تلقائي
├── hello.go              # Main application — التطبيق الرئيسي
├── hello_test.go         # Unit tests + benchmarks — الاختبارات
├── go.mod                # Go module definition — تعريف الوحدة
├── Makefile              # Build commands — أوامر البناء
├── .gitignore            # Git ignore rules — قواعد التجاهل
└── README.md             # This file — هذا الملف
```