#!/bin/bash
# Export RTAB-Map databases to 2D occupancy grid maps
# Usage: ./export_maps.sh

set -e
source /opt/ros/humble/setup.bash

OUTPUT_DIR="$HOME/Documents/GitHub/hws_repo/project/results/exported_maps"
mkdir -p "$OUTPUT_DIR"

echo "========================================"
echo "  RTAB-MAP DATABASE EXPORT TOOL"
echo "========================================"
echo ""

# Function to export a database
export_db() {
    local DB_PATH="$1"
    local DB_NAME="$2"

    if [ ! -f "$DB_PATH" ]; then
        echo "[SKIP] $DB_NAME - Database not found"
        return 1
    fi

    echo "[INFO] Exporting: $DB_NAME"
    echo "       Path: $DB_PATH"

    # Get database info
    INFO=$(rtabmap-info "$DB_PATH" 2>&1 | grep -E "Optimized graph:|LTM:" | head -2)
    echo "       $INFO"

    # Export 2D grid map
    OUTPUT_FILE="$OUTPUT_DIR/${DB_NAME}"

    echo "       Exporting to: ${OUTPUT_FILE}.pgm"

    # Use rtabmap-export to create 2D map
    rtabmap-export \
        --images \
        --poses \
        --poses_camera \
        --output "$OUTPUT_FILE" \
        "$DB_PATH" 2>/dev/null || {
            echo "       [WARN] Standard export failed, trying grid export..."
        }

    # Try to export occupancy grid specifically
    if [ -f "${OUTPUT_FILE}.pgm" ]; then
        echo "       [OK] Exported successfully!"
    else
        echo "       [WARN] No PGM output - map may be corrupted"
    fi

    echo ""
}

echo "Exporting databases..."
echo ""

# Export each database
export_db "$HOME/.ros/rtabmap_final_401mb_backup.db" "final_401mb"
export_db "$HOME/.ros/rtabmap_improved_230153.db" "improved_230153"
export_db "$HOME/.ros/rtabmap.db" "current"
export_db "$HOME/.ros/rtabmap_715mb_broken.db" "broken_715mb"

echo "========================================"
echo "  EXPORT COMPLETE"
echo "========================================"
echo ""
echo "Output directory: $OUTPUT_DIR"
echo ""
ls -la "$OUTPUT_DIR" 2>/dev/null || echo "(empty)"
echo ""
