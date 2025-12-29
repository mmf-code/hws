#!/bin/bash

# RTAB-Map Database Verification Script
# Checks if the recorded map is valid and provides useful information

echo "=========================================="
echo "RTAB-Map Database Verification"
echo "=========================================="
echo ""

MAP_FILE="$HOME/.ros/rtabmap.db"

if [ ! -f "$MAP_FILE" ]; then
    echo "❌ ERROR: Map database not found at $MAP_FILE"
    echo ""
    echo "Steps to create a map:"
    echo "  1. roslaunch robot_project optimized_slam.launch.py"
    echo "  2. In another terminal: ros2 run teleop_twist_keyboard teleop_twist_keyboard"
    echo "  3. Drive around for 3-5 minutes"
    echo "  4. Ctrl+C to save (map should be saved automatically)"
    exit 1
fi

echo "✓ Map database found at: $MAP_FILE"
echo ""

# Check file type
echo "Database Type:"
file "$MAP_FILE"
echo ""

# Check file size
echo "Database Size:"
du -h "$MAP_FILE"
echo ""

# Check modification time
echo "Last Modified:"
stat -c "  %y" "$MAP_FILE" 2>/dev/null || stat -f "  %Sm" "$MAP_FILE" 2>/dev/null
echo ""

# Try to validate SQLite database
if command -v sqlite3 &> /dev/null; then
    echo "Validating SQLite database..."
    RESULT=$(sqlite3 "$MAP_FILE" "PRAGMA integrity_check;" 2>&1)
    if [ "$RESULT" = "ok" ]; then
        echo "✓ Database integrity check: PASSED"
    else
        echo "❌ Database integrity check: FAILED"
        echo "  Result: $RESULT"
        echo "  The database may be corrupted. Try recording again."
    fi
else
    echo "Note: sqlite3 not found. Install it with: sudo apt install sqlite3"
fi

echo ""
echo "=========================================="
echo "To use this map for navigation:"
echo "=========================================="
echo ""
echo "ros2 launch robot_project localization_navigation.launch.py"
echo ""
echo "Then in another terminal:"
echo "ros2 run robot_project random_waypoint_nav"
echo ""
echo "=========================================="
