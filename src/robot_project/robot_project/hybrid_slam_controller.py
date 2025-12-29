#!/usr/bin/env python3
"""
Hybrid SLAM Controller - PyGame-based manual/auto control for SLAM mapping

Modes:
- AUTO: Depth-based autonomous exploration with obstacle avoidance
- MANUAL: Direct WASD control (no obstacle avoidance - be careful!)
- TURBO: Auto mode with 2x speed multiplier

Controls:
- WASD: Move forward/left/backward/right
- 1-5: Speed levels (0.2x to 2.0x)
- Q/E: 90 degree left/right spin
- R: 180 degree U-turn
- SPACE: Toggle Auto/Manual mode
- T: Turbo mode toggle
- ESC: Emergency stop
- C: Return to center
- P: Pause/Resume

Usage:
    ros2 run robot_project hybrid_slam_controller
    ros2 run robot_project hybrid_slam_controller --ros-args -p start_mode:=manual
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import numpy as np
import math
import threading
import time
import signal
import sys

# PyGame import with fallback
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("WARNING: pygame not installed. Run: pip install pygame")


class HybridSlamController(Node):
    def __init__(self):
        super().__init__('hybrid_slam_controller')

        if not PYGAME_AVAILABLE:
            self.get_logger().error('PyGame not available! Install with: pip install pygame')
            raise RuntimeError('PyGame required')

        # ==================== PARAMETERS ====================
        self.declare_parameter('start_mode', 'auto')  # 'auto', 'manual', 'turbo'
        self.declare_parameter('base_linear_speed', 0.9)
        self.declare_parameter('base_angular_speed', 1.8)
        self.declare_parameter('min_distance', 0.8)
        self.declare_parameter('critical_distance', 0.4)
        self.declare_parameter('start_delay', 3.0)

        self.base_linear = self.get_parameter('base_linear_speed').value
        self.base_angular = self.get_parameter('base_angular_speed').value
        self.min_distance = self.get_parameter('min_distance').value
        self.critical_distance = self.get_parameter('critical_distance').value
        start_mode = self.get_parameter('start_mode').value

        # ==================== STATE ====================
        # Mode: 'auto', 'manual', 'turbo'
        self.mode = start_mode
        self.paused = False
        self.emergency_stop = False

        # Speed multipliers (5 levels)
        self.speed_levels = [0.2, 0.5, 1.0, 1.5, 2.0]
        self.speed_level = 2  # Default: 1.0x (index 2)

        # Key states
        self.keys_pressed = {
            'w': False, 'a': False, 's': False, 'd': False,
            'q': False, 'e': False, 'r': False,
        }

        # Robot state
        self.current_x = 2.0
        self.current_y = 0.0
        self.current_yaw = 0.0
        self.total_distance = 0.0
        self.last_x = 2.0
        self.last_y = 0.0

        # Depth sensing (5 regions)
        self.far_left_dist = float('inf')
        self.left_dist = float('inf')
        self.center_dist = float('inf')
        self.right_dist = float('inf')
        self.far_right_dist = float('inf')

        # Stuck detection
        self.stuck_counter = 0
        self.last_center_dist = float('inf')
        self.last_turn_dir = 1  # 1=left, -1=right

        # Special action state
        self.spinning = False
        self.spin_target = 0.0

        # Shutdown flag
        self._shutdown = False

        # ==================== ROS2 ====================
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.depth_sub = self.create_subscription(
            Image, '/camera/rgbd_camera/depth/image_raw', self.depth_callback, 10)
        self.odom_sub = self.create_subscription(
            Odometry, '/odometry/filtered', self.odom_callback, 10)

        self.bridge = CvBridge()

        # Control timer (10 Hz)
        self.control_timer = self.create_timer(0.1, self.control_loop)

        # ==================== PYGAME ====================
        self.window_width = 500
        self.window_height = 400
        self.pygame_thread = threading.Thread(target=self.pygame_loop, daemon=True)
        self.pygame_running = True

        # Start after delay
        self.get_logger().info('=' * 60)
        self.get_logger().info('  HYBRID SLAM CONTROLLER')
        self.get_logger().info(f'  Starting in {start_mode.upper()} mode')
        self.get_logger().info('  PyGame window will open shortly...')
        self.get_logger().info('=' * 60)

        start_delay = self.get_parameter('start_delay').value
        self.startup_timer = self.create_timer(start_delay, self.start_controller)

    def start_controller(self):
        """Start the controller after delay"""
        self.startup_timer.cancel()
        self.pygame_thread.start()
        self.get_logger().info('Controller started! Focus PyGame window for keyboard control.')

    # ==================== CALLBACKS ====================

    def odom_callback(self, msg):
        """Track robot position"""
        self.current_x = msg.pose.pose.position.x
        self.current_y = msg.pose.pose.position.y

        # Extract yaw from quaternion
        q = msg.pose.pose.orientation
        siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        self.current_yaw = math.atan2(siny_cosp, cosy_cosp)

        # Track distance
        dx = self.current_x - self.last_x
        dy = self.current_y - self.last_y
        self.total_distance += math.sqrt(dx*dx + dy*dy)
        self.last_x = self.current_x
        self.last_y = self.current_y

    def depth_callback(self, msg):
        """Process depth image with 5-region detection"""
        try:
            depth_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='passthrough')
            h, w = depth_image.shape[:2]

            # Vertical band (30% to 70%)
            v_start = int(h * 0.30)
            v_end = int(h * 0.70)

            # 5 horizontal regions
            w1 = int(w * 0.15)
            w2 = int(w * 0.35)
            w3 = int(w * 0.65)
            w4 = int(w * 0.85)

            self.far_left_dist = self._get_min_distance(depth_image[v_start:v_end, 0:w1])
            self.left_dist = self._get_min_distance(depth_image[v_start:v_end, w1:w2])
            self.center_dist = self._get_min_distance(depth_image[v_start:v_end, w2:w3])
            self.right_dist = self._get_min_distance(depth_image[v_start:v_end, w3:w4])
            self.far_right_dist = self._get_min_distance(depth_image[v_start:v_end, w4:w])

        except Exception:
            pass

    def _get_min_distance(self, region):
        """Get minimum valid distance from depth region"""
        valid = np.isfinite(region) & (region > 0.15) & (region < 10.0)
        if np.any(valid):
            return float(np.min(region[valid]))
        return float('inf')

    # ==================== CONTROL LOOP ====================

    def control_loop(self):
        """Main 10Hz control loop"""
        if self._shutdown or self.paused:
            self.stop_robot()
            return

        if self.emergency_stop:
            self.stop_robot()
            return

        # Handle special spinning actions
        if self.spinning:
            self._execute_spin()
            return

        twist = Twist()

        if self.mode == 'manual':
            twist = self._manual_control()
        elif self.mode == 'auto':
            twist = self._auto_control(1.0)
        elif self.mode == 'turbo':
            twist = self._auto_control(2.0)

        self.cmd_vel_pub.publish(twist)

    def _manual_control(self):
        """Direct WASD control - no obstacle avoidance!"""
        twist = Twist()
        multiplier = self.speed_levels[self.speed_level]

        linear = self.base_linear * multiplier
        angular = self.base_angular * multiplier

        # Forward/Backward
        if self.keys_pressed['w']:
            twist.linear.x = linear
        elif self.keys_pressed['s']:
            twist.linear.x = -linear * 0.5  # Slower reverse

        # Left/Right turn
        if self.keys_pressed['a']:
            twist.angular.z = angular
        elif self.keys_pressed['d']:
            twist.angular.z = -angular

        return twist

    def _auto_control(self, turbo_mult=1.0):
        """Depth-based autonomous control with obstacle avoidance"""
        twist = Twist()
        multiplier = self.speed_levels[self.speed_level] * turbo_mult

        linear = self.base_linear * multiplier
        angular = self.base_angular * multiplier

        # Stuck detection
        if abs(self.center_dist - self.last_center_dist) < 0.05 and self.center_dist < self.min_distance:
            self.stuck_counter += 1
        else:
            self.stuck_counter = 0
        self.last_center_dist = self.center_dist

        left_space = min(self.far_left_dist, self.left_dist)
        right_space = min(self.far_right_dist, self.right_dist)

        # STUCK RECOVERY
        if self.stuck_counter > 15:
            twist.linear.x = -0.15
            twist.angular.z = angular * 1.5 * self.last_turn_dir
            if self.stuck_counter > 30:
                self.stuck_counter = 0
                self.last_turn_dir *= -1

        # CORNER DETECTION
        elif (self.center_dist < self.critical_distance and
              self.left_dist < self.min_distance and
              self.right_dist < self.min_distance):
            twist.linear.x = -0.08
            if self.far_left_dist > self.far_right_dist:
                twist.angular.z = angular * 1.3
                self.last_turn_dir = 1
            else:
                twist.angular.z = -angular * 1.3
                self.last_turn_dir = -1

        # CRITICAL
        elif self.center_dist < self.critical_distance:
            twist.linear.x = 0.0
            if left_space > right_space:
                twist.angular.z = angular * 1.2
                self.last_turn_dir = 1
            else:
                twist.angular.z = -angular * 1.2
                self.last_turn_dir = -1

        # APPROACHING
        elif self.center_dist < self.min_distance:
            twist.linear.x = linear * 0.3
            if left_space > right_space:
                twist.angular.z = angular * 0.9
                self.last_turn_dir = 1
            else:
                twist.angular.z = -angular * 0.9
                self.last_turn_dir = -1

        # WALL LEFT
        elif self.left_dist < self.min_distance and self.right_dist >= self.min_distance:
            twist.linear.x = linear * 0.8
            twist.angular.z = -angular * 0.5

        # WALL RIGHT
        elif self.right_dist < self.min_distance and self.left_dist >= self.min_distance:
            twist.linear.x = linear * 0.8
            twist.angular.z = angular * 0.5

        # NARROW CORRIDOR
        elif self.left_dist < self.min_distance and self.right_dist < self.min_distance:
            twist.linear.x = linear * 0.6
            diff = self.left_dist - self.right_dist
            twist.angular.z = diff * 1.0

        # CLEAR PATH
        else:
            twist.linear.x = linear
            twist.angular.z = 0.0

        return twist

    # ==================== SPECIAL ACTIONS ====================

    def start_spin(self, degrees):
        """Start a spin action (90, -90, or 180 degrees)"""
        self.spinning = True
        self.spin_target = self.current_yaw + math.radians(degrees)
        # Normalize
        while self.spin_target > math.pi:
            self.spin_target -= 2 * math.pi
        while self.spin_target < -math.pi:
            self.spin_target += 2 * math.pi

    def _execute_spin(self):
        """Execute spinning action"""
        twist = Twist()

        angle_diff = self.spin_target - self.current_yaw
        while angle_diff > math.pi:
            angle_diff -= 2 * math.pi
        while angle_diff < -math.pi:
            angle_diff += 2 * math.pi

        if abs(angle_diff) < 0.1:  # ~5 degrees tolerance
            self.spinning = False
            self.stop_robot()
            return

        # Spin at moderate speed
        twist.angular.z = 1.5 if angle_diff > 0 else -1.5
        self.cmd_vel_pub.publish(twist)

    def stop_robot(self):
        """Stop the robot"""
        twist = Twist()
        self.cmd_vel_pub.publish(twist)

    # ==================== PYGAME ====================

    def pygame_loop(self):
        """PyGame main loop for keyboard input and display"""
        pygame.init()
        screen = pygame.display.set_mode((self.window_width, self.window_height))
        pygame.display.set_caption('SLAM Hybrid Controller')
        clock = pygame.time.Clock()

        # Fonts
        font_large = pygame.font.Font(None, 36)
        font_medium = pygame.font.Font(None, 28)
        font_small = pygame.font.Font(None, 24)

        # Colors
        BG_COLOR = (30, 30, 40)
        WHITE = (255, 255, 255)
        GREEN = (0, 255, 100)
        RED = (255, 80, 80)
        YELLOW = (255, 220, 0)
        BLUE = (100, 150, 255)
        GRAY = (100, 100, 100)
        DARK_GRAY = (50, 50, 60)

        while self.pygame_running and not self._shutdown:
            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._shutdown = True
                    break

                elif event.type == pygame.KEYDOWN:
                    key = pygame.key.name(event.key).lower()

                    # Movement keys
                    if key in self.keys_pressed:
                        self.keys_pressed[key] = True

                    # Speed levels
                    if key in ['1', '2', '3', '4', '5']:
                        self.speed_level = int(key) - 1

                    # Mode switching
                    if key == 'space':
                        if self.mode == 'auto':
                            self.mode = 'manual'
                        elif self.mode == 'manual':
                            self.mode = 'auto'
                        elif self.mode == 'turbo':
                            self.mode = 'auto'
                        self.get_logger().info(f'Mode: {self.mode.upper()}')

                    if key == 't':
                        if self.mode != 'turbo':
                            self.mode = 'turbo'
                        else:
                            self.mode = 'auto'
                        self.get_logger().info(f'Mode: {self.mode.upper()}')

                    # Special actions
                    if key == 'q' and not self.spinning:
                        self.start_spin(90)
                    if key == 'e' and not self.spinning:
                        self.start_spin(-90)
                    if key == 'r' and not self.spinning:
                        self.start_spin(180)

                    # Pause
                    if key == 'p':
                        self.paused = not self.paused
                        self.get_logger().info(f'{"PAUSED" if self.paused else "RESUMED"}')

                    # Emergency stop
                    if key == 'escape':
                        self.emergency_stop = not self.emergency_stop
                        if self.emergency_stop:
                            self.get_logger().warn('EMERGENCY STOP!')
                        else:
                            self.get_logger().info('Emergency stop released')

                elif event.type == pygame.KEYUP:
                    key = pygame.key.name(event.key).lower()
                    if key in self.keys_pressed:
                        self.keys_pressed[key] = False

            # ==================== DRAWING ====================
            screen.fill(BG_COLOR)

            # Title
            title = font_large.render('SLAM HYBRID CONTROLLER', True, WHITE)
            screen.blit(title, (self.window_width//2 - title.get_width()//2, 10))

            # Mode badge
            mode_colors = {'auto': GREEN, 'manual': YELLOW, 'turbo': RED}
            mode_color = mode_colors.get(self.mode, WHITE)
            mode_text = font_medium.render(f'MODE: {self.mode.upper()}', True, mode_color)
            screen.blit(mode_text, (20, 50))

            # Emergency/Pause status
            if self.emergency_stop:
                status = font_medium.render('!! EMERGENCY STOP !!', True, RED)
                screen.blit(status, (250, 50))
            elif self.paused:
                status = font_medium.render('PAUSED', True, YELLOW)
                screen.blit(status, (300, 50))
            elif self.spinning:
                status = font_medium.render('SPINNING...', True, BLUE)
                screen.blit(status, (300, 50))

            # Speed bar
            speed_label = font_small.render('Speed:', True, WHITE)
            screen.blit(speed_label, (20, 85))
            for i in range(5):
                color = GREEN if i <= self.speed_level else DARK_GRAY
                pygame.draw.rect(screen, color, (90 + i*40, 85, 35, 20))
                level_text = font_small.render(f'{self.speed_levels[i]}x', True, WHITE if i <= self.speed_level else GRAY)
                screen.blit(level_text, (93 + i*40, 87))

            # Controls help
            y_offset = 120
            controls = [
                ('WASD', 'Move'),
                ('1-5', 'Speed'),
                ('Q/E', '90 Turn'),
                ('R', '180 Turn'),
                ('SPACE', 'Auto/Manual'),
                ('T', 'Turbo'),
                ('P', 'Pause'),
                ('ESC', 'E-Stop'),
            ]
            pygame.draw.rect(screen, DARK_GRAY, (15, y_offset-5, 230, 145), border_radius=5)
            for i, (key, action) in enumerate(controls):
                key_text = font_small.render(f'[{key}]', True, YELLOW)
                action_text = font_small.render(action, True, WHITE)
                screen.blit(key_text, (25, y_offset + i*17))
                screen.blit(action_text, (100, y_offset + i*17))

            # Active keys indicator
            pygame.draw.rect(screen, DARK_GRAY, (260, y_offset-5, 220, 80), border_radius=5)
            keys_title = font_small.render('Active Keys:', True, WHITE)
            screen.blit(keys_title, (270, y_offset))

            # WASD visual
            key_positions = {'w': (350, y_offset+20), 'a': (320, y_offset+45), 's': (350, y_offset+45), 'd': (380, y_offset+45)}
            for key, pos in key_positions.items():
                color = GREEN if self.keys_pressed[key] else GRAY
                pygame.draw.rect(screen, color, (pos[0], pos[1], 25, 25), border_radius=3)
                key_label = font_small.render(key.upper(), True, WHITE)
                screen.blit(key_label, (pos[0]+7, pos[1]+3))

            # Robot info
            y_info = 280
            pygame.draw.rect(screen, DARK_GRAY, (15, y_info-5, 470, 110), border_radius=5)

            pos_text = font_small.render(f'Position: x={self.current_x:.2f}  y={self.current_y:.2f}  yaw={math.degrees(self.current_yaw):.1f}', True, WHITE)
            screen.blit(pos_text, (25, y_info))

            dist_text = font_small.render(f'Distance traveled: {self.total_distance:.1f} m', True, WHITE)
            screen.blit(dist_text, (25, y_info + 22))

            # Depth readings with color coding
            depths = [
                ('FL', self.far_left_dist),
                ('L', self.left_dist),
                ('C', self.center_dist),
                ('R', self.right_dist),
                ('FR', self.far_right_dist),
            ]
            depth_label = font_small.render('Depth:', True, WHITE)
            screen.blit(depth_label, (25, y_info + 48))

            x_pos = 90
            for label, dist in depths:
                if dist < self.critical_distance:
                    color = RED
                elif dist < self.min_distance:
                    color = YELLOW
                else:
                    color = GREEN
                dist_str = f'{dist:.1f}' if dist < 10 else 'inf'
                depth_text = font_small.render(f'{label}:{dist_str}', True, color)
                screen.blit(depth_text, (x_pos, y_info + 48))
                x_pos += 75

            # Current velocity
            multiplier = self.speed_levels[self.speed_level]
            turbo = 2.0 if self.mode == 'turbo' else 1.0
            actual_linear = self.base_linear * multiplier * turbo
            actual_angular = self.base_angular * multiplier * turbo
            vel_text = font_small.render(f'Max velocity: {actual_linear:.2f} m/s  |  {math.degrees(actual_angular):.0f} deg/s', True, BLUE)
            screen.blit(vel_text, (25, y_info + 75))

            pygame.display.flip()
            clock.tick(30)  # 30 FPS

        pygame.quit()

    def shutdown(self):
        """Graceful shutdown"""
        self._shutdown = True
        self.pygame_running = False
        self.stop_robot()
        self.get_logger().info('Shutting down...')


# Global reference for signal handler
_node = None


def signal_handler(signum, frame):
    global _node
    if _node is not None:
        _node.shutdown()
    sys.exit(0)


def main(args=None):
    global _node

    rclpy.init(args=args)

    try:
        _node = HybridSlamController()
    except RuntimeError as e:
        print(f'Error: {e}')
        rclpy.shutdown()
        return

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        rclpy.spin(_node)
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        if _node is not None:
            _node.shutdown()
            _node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
