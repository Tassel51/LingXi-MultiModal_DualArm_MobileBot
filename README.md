# LingXi-MultiModal-DualArm-MobileBot
Multi-modal perception & mobile manipulation system for dual-arm autonomous robot.

## Overview
This project implements a multi-modal perception and motion control framework for a dual-arm mobile robot platform. It integrates visual perception, natural language understanding, environment modeling, and end-to-end robot control to achieve autonomous mobile manipulation tasks.

## Features
- Multi-modal input: RGB camera, depth sensing, audio / command understanding
- Dual-arm cooperative motion planning and trajectory generation
- Mobile base autonomous navigation and obstacle avoidance
- Real-time environment perception and target localization
- Modular software architecture for easy deployment and extension

## System Architecture
1. **Perception Module**: Object detection, semantic segmentation, pose estimation
2. **Decision & Planning Module**: Task parsing, motion planning, collision checking
3. **Control Module**: Low-level robot arm & mobile base control
4. **Fusion Module**: Multi-modal information alignment and state estimation

## Tech Stack
- Python / C++
- ROS / ROS2
- PyTorch (deep learning inference)
- OpenCV, Open3D
- Linux, Ubuntu

## Project Structure
```plaintext
├── src/                # Core algorithm and control code
├── perception/         # Visual & multi-modal perception
├── planning/           # Motion & task planning
├── control/            # Robot arm & base driver
├── config/             # Parameter configuration
└── launch/             # Startup scripts
