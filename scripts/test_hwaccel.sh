#!/bin/bash

# Hardware Acceleration Test Script
# This script tests if hardware acceleration is properly set up and working

echo "==========================================="
echo "Trailarr Hardware Acceleration Test"
echo "==========================================="

# Test 1: Check ffmpeg installation and version
echo "1. Checking ffmpeg installation..."
if command -v ffmpeg &> /dev/null; then
    echo "✓ ffmpeg is installed"
    ffmpeg -version | head -n 1
else
    echo "✗ ffmpeg not found"
    exit 1
fi

echo ""

# Test 2: Check available encoders
echo "2. Checking available hardware encoders..."
echo "NVIDIA encoders:"
ffmpeg -encoders 2>/dev/null | grep nvenc || echo "  No NVIDIA encoders found"
echo "VAAPI encoders:"
ffmpeg -encoders 2>/dev/null | grep vaapi || echo "  No VAAPI encoders found"
echo "AMF encoders:"
ffmpeg -encoders 2>/dev/null | grep amf || echo "  No AMF encoders found"

echo ""

# Test 3: Check GPU devices
echo "3. Checking GPU device availability..."

# NVIDIA
echo "NVIDIA GPU:"
if command -v nvidia-smi &> /dev/null; then
    if nvidia-smi > /dev/null 2>&1; then
        echo "✓ NVIDIA GPU detected"
        nvidia-smi --query-gpu=name --format=csv,noheader | head -1
    else
        echo "✗ nvidia-smi failed"
    fi
else
    echo "  nvidia-smi not available"
fi

# DRI devices for Intel/AMD
echo "DRI devices:"
if [ -d /dev/dri ]; then
    DRI_DEVICES=$(ls /dev/dri/ 2>/dev/null)
    if [ -n "$DRI_DEVICES" ]; then
        echo "✓ DRI devices found:"
        ls -la /dev/dri/
    else
        echo "✗ No DRI devices found"
    fi
else
    echo "  /dev/dri not available"
fi

echo ""

# Test 4: VAAPI capability test
echo "4. Testing VAAPI capability..."
if command -v vainfo &> /dev/null && [ -e /dev/dri/renderD128 ]; then
    echo "✓ vainfo available, testing..."
    if vainfo --display drm --device /dev/dri/renderD128 2>/dev/null | grep -q "VAProfile"; then
        echo "✓ VAAPI profiles detected:"
        vainfo --display drm --device /dev/dri/renderD128 2>/dev/null | grep "VAProfile" | head -5
    else
        echo "✗ No VAAPI profiles found"
    fi
else
    echo "  vainfo or DRI device not available"
fi

echo ""

# Test 5: Check user permissions
echo "5. Checking user permissions..."
if [ -e /dev/dri/renderD128 ]; then
    if [ -r /dev/dri/renderD128 ] && [ -w /dev/dri/renderD128 ]; then
        echo "✓ User has read/write access to render device"
    else
        echo "⚠ User may not have proper render device access"
        ls -la /dev/dri/renderD128
    fi
else
    echo "  No render device to test"
fi

echo ""

# Test 6: Simple encoding test (optional)
echo "6. Hardware acceleration encoding test..."
echo "Creating test pattern..."

# Create a simple test video
if ffmpeg -f lavfi -i testsrc=duration=2:size=320x240:rate=30 -pix_fmt yuv420p /tmp/test_input.mkv -y > /dev/null 2>&1; then
    echo "✓ Test input created"
    
    # Test NVIDIA encoding
    if ffmpeg -encoders 2>/dev/null | grep -q h264_nvenc; then
        echo "Testing NVIDIA h264_nvenc..."
        if ffmpeg -hwaccel cuda -hwaccel_output_format cuda -i /tmp/test_input.mkv -c:v h264_nvenc -preset fast -cq 30 /tmp/test_nvenc.mkv -y > /dev/null 2>&1; then
            echo "✓ NVIDIA encoding test passed"
            rm -f /tmp/test_nvenc.mkv
        else
            echo "✗ NVIDIA encoding test failed"
        fi
    fi
    
    # Test VAAPI encoding
    if ffmpeg -encoders 2>/dev/null | grep -q h264_vaapi && [ -e /dev/dri/renderD128 ]; then
        echo "Testing VAAPI h264_vaapi..."
        if ffmpeg -hwaccel vaapi -hwaccel_device /dev/dri/renderD128 -i /tmp/test_input.mkv -vf format=nv12,hwupload -c:v h264_vaapi -qp 30 -b:v 0 /tmp/test_vaapi.mkv -y > /dev/null 2>&1; then
            echo "✓ VAAPI encoding test passed"
            rm -f /tmp/test_vaapi.mkv
        else
            echo "✗ VAAPI encoding test failed"
        fi
    fi
    
    # Cleanup
    rm -f /tmp/test_input.mkv
else
    echo "✗ Could not create test input"
fi

echo ""
echo "==========================================="
echo "Hardware acceleration test completed"
echo "==========================================="