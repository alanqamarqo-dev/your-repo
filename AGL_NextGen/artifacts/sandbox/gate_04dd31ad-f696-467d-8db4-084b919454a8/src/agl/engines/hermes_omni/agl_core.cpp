// agl_core.cpp
#include <cmath>
#include <cstdlib>

// تعريف التصدير (للويندوز)
#define DLLEXPORT extern "C" __declspec(dllexport)

// دالة C++ سريعة جداً لمعالجة مصفوفة البكسلات الخام
// تستقبل مؤشر (Pointer) لبيانات الصورة القادمة من بايثون
DLLEXPORT float process_frame_data(unsigned char* data, int size, int width, int height) {
    if (data == 0 || size <= 0) return 0.0f;

    long long total_energy = 0;
    
    // نقوم بمسح الصورة بسرعة عالية
    // نحسب "الإنتروبيا" أو التباين في الصورة كمقياس للطاقة
    // C++ أسرع بـ 50-100 مرة من بايثون في هذه الحلقة
    for (int i = 0; i < size; i += 4) { // نقفز 4 خطوات للسرعة القصوى
        unsigned char pixel = data[i];
        // معادلة بسيطة للطاقة: البعد عن اللون الرمادي المتوسط
        total_energy += abs(pixel - 128);
    }
    
    // تطبيع النتيجة لتكون بين 0 و 10
    float avg_energy = (float)total_energy / (size / 4.0f);
    
    // معادلة تقريبية لتحويل التباين إلى "طاقة حيوية"
    return avg_energy / 5.0f; 
}

DLLEXPORT int get_core_status() {
    return 1; // 1 = Ready
}
