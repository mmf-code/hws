#!/usr/bin/env python3
"""
SLAM Comparison Script - Compare RGBD vs ICP SLAM performance

Reads CSV files from evaluation_node and map_metrics, generates comparison tables.

Usage:
    ros2 run robot_project slam_comparison
    ros2 run robot_project slam_comparison --ros-args -p data_dir:=project/results/data
"""

import os
import csv
import glob
from datetime import datetime


def find_latest_files(data_dir, prefix, slam_mode):
    """Find the latest CSV file for a given prefix and SLAM mode"""
    pattern = os.path.join(data_dir, f'{prefix}_{slam_mode}_*.csv')
    files = glob.glob(pattern)
    if not files:
        return None
    return max(files, key=os.path.getctime)


def read_csv_last_row(filepath):
    """Read the last row of a CSV file as a dictionary"""
    if not filepath or not os.path.exists(filepath):
        return None

    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        if rows:
            return rows[-1]
    return None


def read_csv_all_rows(filepath):
    """Read all rows of a CSV file"""
    if not filepath or not os.path.exists(filepath):
        return []

    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        return list(reader)


def calculate_average_metrics(rows):
    """Calculate average of numeric metrics from rows"""
    if not rows:
        return {}

    numeric_fields = [
        'ekf_rmse', 'ekf_ate', 'ekf_rpe', 'ekf_max', 'ekf_std',
        'slam_rmse', 'slam_ate', 'slam_rpe', 'slam_max', 'slam_std',
        'density_3d', 'density_2d', 'coverage_2d', 'volume',
        'bbox_x', 'bbox_y', 'bbox_z'
    ]

    averages = {}
    for field in numeric_fields:
        values = []
        for row in rows:
            if field in row:
                try:
                    values.append(float(row[field]))
                except (ValueError, TypeError):
                    pass
        if values:
            averages[field] = sum(values) / len(values)

    return averages


def print_comparison_table(rgbd_metrics, icp_metrics, title):
    """Print a comparison table"""
    print(f'\n{"="*60}')
    print(f' {title}')
    print(f'{"="*60}')
    print(f'{"Metric":<20} {"RGBD":>15} {"ICP":>15} {"Diff":>10}')
    print(f'{"-"*60}')

    # Combine all keys
    all_keys = set()
    if rgbd_metrics:
        all_keys.update(rgbd_metrics.keys())
    if icp_metrics:
        all_keys.update(icp_metrics.keys())

    for key in sorted(all_keys):
        rgbd_val = rgbd_metrics.get(key, 0) if rgbd_metrics else 0
        icp_val = icp_metrics.get(key, 0) if icp_metrics else 0

        # Skip non-numeric or timestamp fields
        if key in ['timestamp', 'elapsed_time', 'slam_mode']:
            continue
        if key == 'num_points':
            print(f'{key:<20} {int(rgbd_val):>15,} {int(icp_val):>15,} {int(icp_val - rgbd_val):>10,}')
        else:
            try:
                rgbd_f = float(rgbd_val)
                icp_f = float(icp_val)
                diff = icp_f - rgbd_f
                print(f'{key:<20} {rgbd_f:>15.4f} {icp_f:>15.4f} {diff:>+10.4f}')
            except (ValueError, TypeError):
                pass

    print(f'{"="*60}')


def generate_report(data_dir):
    """Generate a full comparison report"""
    print('\n')
    print('='*70)
    print(' KON414E FINAL PROJECT - SLAM COMPARISON REPORT')
    print(' Team 14: Ceylan Tolunay, Atakan Yaman, Eren Yücetürk')
    print(f' Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print('='*70)

    # Find localization metrics files
    rgbd_metrics_file = find_latest_files(data_dir, 'metrics', 'rgbd')
    icp_metrics_file = find_latest_files(data_dir, 'metrics', 'icp')

    print(f'\nData directory: {data_dir}')
    print(f'RGBD metrics file: {os.path.basename(rgbd_metrics_file) if rgbd_metrics_file else "Not found"}')
    print(f'ICP metrics file: {os.path.basename(icp_metrics_file) if icp_metrics_file else "Not found"}')

    # Localization comparison (Requirement 5)
    print('\n' + '='*70)
    print(' REQUIREMENT 5: Localization Performance Comparison')
    print('='*70)

    rgbd_loc = read_csv_last_row(rgbd_metrics_file)
    icp_loc = read_csv_last_row(icp_metrics_file)

    if rgbd_loc or icp_loc:
        print_comparison_table(rgbd_loc, icp_loc, 'Localization Metrics (vs Ground Truth)')

        # Winner analysis
        print('\nAnalysis:')
        if rgbd_loc and icp_loc:
            rgbd_rmse = float(rgbd_loc.get('ekf_rmse', 999))
            icp_rmse = float(icp_loc.get('ekf_rmse', 999))
            if rgbd_rmse < icp_rmse:
                print(f'  - RGBD has lower RMSE ({rgbd_rmse:.4f}m vs {icp_rmse:.4f}m)')
            else:
                print(f'  - ICP has lower RMSE ({icp_rmse:.4f}m vs {rgbd_rmse:.4f}m)')

            rgbd_ate = float(rgbd_loc.get('ekf_ate', 999))
            icp_ate = float(icp_loc.get('ekf_ate', 999))
            if rgbd_ate < icp_ate:
                print(f'  - RGBD has lower ATE ({rgbd_ate:.4f}m vs {icp_ate:.4f}m)')
            else:
                print(f'  - ICP has lower ATE ({icp_ate:.4f}m vs {rgbd_ate:.4f}m)')
    else:
        print('  No localization data found. Run evaluation_node with both SLAM modes.')

    # Map metrics comparison (Requirement 6)
    print('\n' + '='*70)
    print(' REQUIREMENT 6: 3D Mapping Performance Comparison')
    print('='*70)

    rgbd_map_file = find_latest_files(data_dir, 'map_metrics', 'rgbd')
    icp_map_file = find_latest_files(data_dir, 'map_metrics', 'icp')

    print(f'RGBD map metrics: {os.path.basename(rgbd_map_file) if rgbd_map_file else "Not found"}')
    print(f'ICP map metrics: {os.path.basename(icp_map_file) if icp_map_file else "Not found"}')

    rgbd_map = read_csv_last_row(rgbd_map_file)
    icp_map = read_csv_last_row(icp_map_file)

    if rgbd_map or icp_map:
        print_comparison_table(rgbd_map, icp_map, 'Map Quality Metrics')

        # Analysis
        print('\nAnalysis:')
        if rgbd_map and icp_map:
            rgbd_pts = int(rgbd_map.get('num_points', 0))
            icp_pts = int(icp_map.get('num_points', 0))
            if rgbd_pts > icp_pts:
                print(f'  - RGBD has more points ({rgbd_pts:,} vs {icp_pts:,})')
            else:
                print(f'  - ICP has more points ({icp_pts:,} vs {rgbd_pts:,})')

            rgbd_density = float(rgbd_map.get('density_3d', 0))
            icp_density = float(icp_map.get('density_3d', 0))
            if rgbd_density > icp_density:
                print(f'  - RGBD has higher density ({rgbd_density:.2f} vs {icp_density:.2f} pts/m³)')
            else:
                print(f'  - ICP has higher density ({icp_density:.2f} vs {rgbd_density:.2f} pts/m³)')

            rgbd_cov = float(rgbd_map.get('coverage_2d', 0))
            icp_cov = float(icp_map.get('coverage_2d', 0))
            if rgbd_cov > icp_cov:
                print(f'  - RGBD has more coverage ({rgbd_cov:.2f} vs {icp_cov:.2f} m²)')
            else:
                print(f'  - ICP has more coverage ({icp_cov:.2f} vs {rgbd_cov:.2f} m²)')
    else:
        print('  No map metrics found. Run map_metrics with both SLAM modes.')

    # Summary table for report
    print('\n' + '='*70)
    print(' SUMMARY TABLE (for IEEE Report)')
    print('='*70)
    print(f'{"Metric":<25} {"RGBD":<15} {"ICP":<15} {"Better"}')
    print('-'*70)

    if rgbd_loc and icp_loc:
        rgbd_rmse = float(rgbd_loc.get('ekf_rmse', 0))
        icp_rmse = float(icp_loc.get('ekf_rmse', 0))
        better = 'RGBD' if rgbd_rmse < icp_rmse else 'ICP'
        print(f'{"EKF RMSE (m)":<25} {rgbd_rmse:<15.4f} {icp_rmse:<15.4f} {better}')

        rgbd_ate = float(rgbd_loc.get('ekf_ate', 0))
        icp_ate = float(icp_loc.get('ekf_ate', 0))
        better = 'RGBD' if rgbd_ate < icp_ate else 'ICP'
        print(f'{"EKF ATE (m)":<25} {rgbd_ate:<15.4f} {icp_ate:<15.4f} {better}')

        rgbd_rpe = float(rgbd_loc.get('ekf_rpe', 0))
        icp_rpe = float(icp_loc.get('ekf_rpe', 0))
        better = 'RGBD' if rgbd_rpe < icp_rpe else 'ICP'
        print(f'{"EKF RPE (m)":<25} {rgbd_rpe:<15.4f} {icp_rpe:<15.4f} {better}')

    if rgbd_map and icp_map:
        rgbd_pts = int(rgbd_map.get('num_points', 0))
        icp_pts = int(icp_map.get('num_points', 0))
        better = 'RGBD' if rgbd_pts > icp_pts else 'ICP'
        print(f'{"Point Count":<25} {rgbd_pts:<15,} {icp_pts:<15,} {better}')

        rgbd_density = float(rgbd_map.get('density_3d', 0))
        icp_density = float(icp_map.get('density_3d', 0))
        better = 'RGBD' if rgbd_density > icp_density else 'ICP'
        print(f'{"3D Density (pts/m³)":<25} {rgbd_density:<15.2f} {icp_density:<15.2f} {better}')

        rgbd_cov = float(rgbd_map.get('coverage_2d', 0))
        icp_cov = float(icp_map.get('coverage_2d', 0))
        better = 'RGBD' if rgbd_cov > icp_cov else 'ICP'
        print(f'{"Coverage (m²)":<25} {rgbd_cov:<15.2f} {icp_cov:<15.2f} {better}')

    print('='*70)
    print('\n')


def main():
    """Main entry point"""
    import argparse
    parser = argparse.ArgumentParser(description='Compare RGBD vs ICP SLAM performance')
    parser.add_argument('--data-dir', '-d', default='project/results/data',
                       help='Directory containing CSV data files')
    args = parser.parse_args()

    # Handle ROS2 args
    data_dir = args.data_dir

    # Check if directory exists
    if not os.path.isdir(data_dir):
        print(f'Error: Directory not found: {data_dir}')
        print('Run the SLAM system first to generate data files.')
        return

    generate_report(data_dir)


if __name__ == '__main__':
    main()
