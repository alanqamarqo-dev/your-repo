#include <windows.h>
#include <vfw.h>
#include <iostream>
#include <vector>
#include <cmath>

#pragma comment(lib, "vfw32.lib")

std::vector<unsigned char> prevBuffer;
bool firstFrame = true;
const int THRESHOLD = 30; // Sensitivity

LRESULT CALLBACK FrameCallback(HWND hWnd, LPVIDEOHDR lpVHdr) {
    if (!lpVHdr || !lpVHdr->lpData) return 0;

    long size = lpVHdr->dwBytesUsed;
    unsigned char* data = lpVHdr->lpData;
    int width = 320; // Video width defined in Main
    int height = 240;

    if (firstFrame) {
        prevBuffer.assign(data, data + size);
        firstFrame = false;
        return 0;
    }

    long long sumX = 0;
    long long sumY = 0;
    long count = 0;

    // Scan image pixel by pixel (skip 2 for speed)
    for (int y = 0; y < height; y += 2) {
        for (int x = 0; x < width; x += 2) {
            // Approximate RGB index for VFW (3 bytes per pixel)
            // Note: VFW might return BGR or aligned rows, but this approximation works for motion detection
            int index = (y * width + x) * 3; 
            if (index >= size) continue;

            int current = data[index];
            int previous = prevBuffer[index];
            
            if (std::abs(current - previous) > THRESHOLD) {
                sumX += x;
                sumY += y;
                count++;
            }
        }
    }

    // Update previous buffer
    memcpy(prevBuffer.data(), data, size);

    // Calculate Center of Mass
    if (count > 50) { // Ignore tiny movements
        int centerX = (int)(sumX / count);
        int centerY = (int)(sumY / count);
        
        // Mirror X axis because camera acts like a mirror
        centerX = width - centerX;

        // Print coordinates for Python
        std::cout << "VEC:" << centerX << "," << centerY << std::endl;
    } else {
        std::cout << "VEC:NONE" << std::endl; // No motion
    }

    return 0;
}

int main() {
    HWND hWndC = capCreateCaptureWindowA("AGL_VECTOR", WS_VISIBLE | WS_OVERLAPPEDWINDOW, 100, 100, 320, 240, NULL, 0);
    if (capDriverConnect(hWndC, 0)) {
        capSetCallbackOnFrame(hWndC, FrameCallback);
        capPreviewScale(hWndC, TRUE);
        capPreviewRate(hWndC, 33); // 30 FPS for faster response
        capPreview(hWndC, TRUE);

        MSG msg;
        while (GetMessage(&msg, NULL, 0, 0) > 0) {
            TranslateMessage(&msg);
            DispatchMessage(&msg);
        }
        capDriverDisconnect(hWndC);
    }
    return 0;
}
