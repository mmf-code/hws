#!/usr/bin/env python3
"""
Auto-backup for RTAB-Map database during SLAM.
Copies database every 2 minutes using SQLite's safe backup API.
"""

import rclpy
from rclpy.node import Node
import sqlite3
import os
import shutil
from datetime import datetime


class MapAutoBackup(Node):
    def __init__(self):
        super().__init__('map_auto_backup')

        self.db_path = os.path.expanduser('~/.ros/rtabmap.db')
        self.backup_dir = os.path.expanduser('~/maps/auto_backups')
        os.makedirs(self.backup_dir, exist_ok=True)

        # Backup every 2 minutes
        self.backup_interval = 120.0
        self.timer = self.create_timer(self.backup_interval, self.backup_database)

        self.backup_count = 0
        self.get_logger().info(f'Map Auto-Backup started. Interval: {self.backup_interval}s')
        self.get_logger().info(f'Backup dir: {self.backup_dir}')

    def backup_database(self):
        if not os.path.exists(self.db_path):
            self.get_logger().warn(f'Database not found: {self.db_path}')
            return

        try:
            # Use SQLite online backup API - safe even while writing
            timestamp = datetime.now().strftime('%H%M%S')
            backup_path = os.path.join(self.backup_dir, f'rtabmap_backup_{timestamp}.db')

            # SQLite safe backup
            source = sqlite3.connect(self.db_path)
            dest = sqlite3.connect(backup_path)
            source.backup(dest)
            source.close()
            dest.close()

            size_mb = os.path.getsize(backup_path) / 1024 / 1024
            self.backup_count += 1

            self.get_logger().info(f'✓ Backup #{self.backup_count}: {size_mb:.1f}MB -> {backup_path}')

            # Keep only last 5 backups
            self.cleanup_old_backups()

        except Exception as e:
            self.get_logger().error(f'Backup failed: {e}')

    def cleanup_old_backups(self):
        backups = sorted([
            f for f in os.listdir(self.backup_dir)
            if f.startswith('rtabmap_backup_') and f.endswith('.db')
        ])

        # Keep last 5
        while len(backups) > 5:
            old = os.path.join(self.backup_dir, backups.pop(0))
            os.remove(old)
            self.get_logger().info(f'Removed old backup: {old}')


def main(args=None):
    rclpy.init(args=args)
    node = MapAutoBackup()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Final backup on shutdown...')
        node.backup_database()
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
