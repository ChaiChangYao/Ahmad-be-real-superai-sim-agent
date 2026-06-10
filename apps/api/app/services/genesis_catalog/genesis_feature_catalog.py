from __future__ import annotations


def get_genesis_feature_catalog() -> dict:
    return {
        "source": "https://github.com/Genesis-Embodied-AI/genesis-world",
        "physics_capabilities": {
            "genesis_supports": [
                "rigid_body_dynamics",
                "articulated_joints",
                "contact_collision",
                "terrain_simulation",
                "multi_solver_coupling",
                "soft_body_and_particles",
            ],
            "buildables_implemented": [
                "rigid_body_dynamics",
                "articulated_joints",
                "contact_collision",
                "terrain_simulation",
                "payload_effects",
                "wire_route_physics_approximation",
            ],
            "not_yet_implemented": [
                "full_ipc_robot_cloth_teleop",
                "full_nyx_pipeline_in_ui",
                "all_upstream_example_exact_parity",
            ],
        },
        "asset_format_capabilities": {
            "genesis_supports": ["urdf", "mjcf", "mesh_assets", "camera_sensors"],
            "buildables_implemented": ["step", "stl", "obj", "glb", "urdf", "mjcf"],
            "not_yet_implemented": ["automatic_asset_format_conversion_for_every_upstream_example"],
        },
        "sensor_capabilities": {
            "genesis_supports": ["imu", "depth", "raycast_like", "contact", "camera_rgb"],
            "buildables_implemented": ["imu_metrics", "sensor_visibility", "contact_ratio", "depth_ray_overlay_preview"],
            "not_yet_implemented": ["native_lidar_artifact_export", "tactile_grid_artifacts"],
        },
        "rendering_capabilities": {
            "genesis_supports": ["camera_sensor_rendering", "nyx_renderer_path"],
            "buildables_implemented": ["frontend_preview_viewport", "run_artifact_paths", "camera_test_catalog_entries"],
            "not_yet_implemented": ["full_nyx_walkthrough_ui", "segmentation_image_pipeline"],
        },
        "environment_capabilities": {
            "genesis_supports": ["flat", "slope", "rough", "steps", "friction_variations"],
            "buildables_implemented": ["flat", "slope", "rough", "steps", "low_friction", "high_friction"],
            "not_yet_implemented": ["granular_sand_scene_authoring_ui", "soft_ground_authoring_ui"],
        },
        "control_capabilities": {
            "genesis_supports": ["joint_targets", "controllers", "parallel_envs"],
            "buildables_implemented": ["robot_dog_remote_control", "scenario_based_control", "joint_command_table_metadata"],
            "not_yet_implemented": ["uploaded_firmware_runtime_execution", "parallel_env_benchmarking_ui"],
        },
    }
