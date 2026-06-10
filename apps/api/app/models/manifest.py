from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field


class Units(BaseModel):
    length: Literal["m"] = "m"
    mass: Literal["kg"] = "kg"
    time: Literal["s"] = "s"
    angle: Literal["rad"] = "rad"


class Vec3(BaseModel):
    x: float
    y: float
    z: float


class Transform(BaseModel):
    position: Vec3 = Field(default_factory=lambda: Vec3(x=0.0, y=0.0, z=0.0))
    rotation_rpy: Vec3 = Field(default_factory=lambda: Vec3(x=0.0, y=0.0, z=0.0))


class Asset(BaseModel):
    id: str
    name: str
    type: Literal["step", "stl", "obj", "glb", "gltf", "urdf", "mjcf", "texture", "other"]
    file_path: str
    original_filename: str
    unit_scale_to_meters: float = 1.0
    visual_only: bool = False
    generated: bool = False
    source_asset_id: str | None = None
    notes: str | None = None


class Material(BaseModel):
    id: str
    name: str
    density_kg_m3: float
    static_friction: float = 0.5
    dynamic_friction: float = 0.4
    restitution: float = 0.1
    youngs_modulus_pa: float | None = None
    yield_strength_pa: float | None = None
    melting_point_c: float | None = None
    thermal_notes: str | None = None
    simulation_notes: str
    source_url: str | None = None
    confidence: Literal["placeholder", "datasheet", "user_provided"] = "placeholder"


class CollisionPrimitive(BaseModel):
    id: str
    link_id: str
    primitive_type: Literal["box", "sphere", "capsule", "cylinder", "convex_hull", "low_poly_mesh"]
    dimensions: list[float]
    offset: Vec3 = Field(default_factory=lambda: Vec3(x=0.0, y=0.0, z=0.0))
    rotation_rpy: Vec3 = Field(default_factory=lambda: Vec3(x=0.0, y=0.0, z=0.0))


class Link(BaseModel):
    id: str
    name: str
    category: Literal["body", "leg", "foot", "bracket", "mount", "electronics_block", "sensor_mount", "wire", "payload", "other"]
    visual_asset_id: str | None = None
    material_id: str
    mass_kg: float
    center_of_mass: Vec3 = Field(default_factory=lambda: Vec3(x=0.0, y=0.0, z=0.0))
    inertia_tensor: list[float] | None = None
    transform: Transform = Field(default_factory=Transform)
    collision_primitive_ids: list[str] = Field(default_factory=list)
    parent_link_id: str | None = None
    editable: bool = True
    notes: str | None = None


class Joint(BaseModel):
    id: str
    name: str
    type: Literal["fixed", "revolute", "continuous", "prismatic", "ball"]
    parent_link_id: str
    child_link_id: str
    origin_xyz: Vec3 = Field(default_factory=lambda: Vec3(x=0.0, y=0.0, z=0.0))
    origin_rpy: Vec3 = Field(default_factory=lambda: Vec3(x=0.0, y=0.0, z=0.0))
    axis_xyz: Vec3 = Field(default_factory=lambda: Vec3(x=0.0, y=0.0, z=1.0))
    limit_lower_rad: float = -1.57
    limit_upper_rad: float = 1.57
    effort_limit_nm: float = 2.0
    velocity_limit_rad_s: float = 2.0
    damping: float = 0.05
    friction: float = 0.01
    auto_detected: bool = False
    user_confirmed: bool = True
    notes: str | None = None


class Actuator(BaseModel):
    id: str
    name: str
    type: Literal["servo", "dc_motor", "stepper", "brushless", "linear_actuator", "virtual_motor"]
    real_component_profile_id: str
    joint_id: str
    control_mode: Literal["position", "velocity", "torque"] = "position"
    max_torque_nm: float
    max_velocity_rad_s: float
    rated_voltage_v: float
    stall_current_a: float
    no_load_current_a: float | None = None
    gear_ratio: float | None = None
    kp: float = 20.0
    kd: float = 1.0
    torque_curve: list[list[float]] | None = None
    mass_kg: float
    dimensions_m: list[float]
    mounting_transform: Transform = Field(default_factory=Transform)
    source_url: str | None = None
    confidence: Literal["placeholder", "datasheet", "manufacturer_page", "user_provided"] = "placeholder"
    notes: str | None = None


class Electronics(BaseModel):
    id: str
    component_profile_id: str
    link_id: str | None = None
    transform: Transform = Field(default_factory=Transform)
    editable: bool = True
    notes: str | None = None


class Sensor(BaseModel):
    id: str
    name: str
    sensor_type: Literal["imu", "camera", "depth_camera", "raycaster", "ultrasonic", "contact", "contact_force", "encoder", "gps", "temperature"]
    attach_link_id: str
    transform: Transform = Field(default_factory=Transform)
    update_rate_hz: float = 30.0
    fov_deg: float | None = None
    range_m: float | None = None
    derived: bool = False


class Wire(BaseModel):
    id: str
    name: str
    from_component_id: str
    to_component_id: str
    route_points: list[Vec3] = Field(default_factory=list)
    mass_kg: float = 0.02
    min_bend_radius_m: float = 0.01


class RobotDescription(BaseModel):
    preferred_format: Literal["urdf", "mjcf"] = "urdf"
    urdf_path: str | None = None
    mjcf_path: str | None = None
    generated_from_manifest: bool = True


class ControlConfig(BaseModel):
    script_path: str | None = None
    built_in_controller: str = "robot_dog_default"


class Scenario(BaseModel):
    id: str
    name: str
    description: str
    duration_s: float = 5.0
    config: dict = Field(default_factory=dict)


class Payload(BaseModel):
    id: str
    name: str
    mass_kg: float = 0.0
    attach_link_id: str | None = None
    offset: Transform = Field(default_factory=Transform)


class RenderCamera(BaseModel):
    id: str
    name: str
    attach_link_id: str | None = None
    transform: Transform = Field(default_factory=Transform)
    fov_deg: float = 60.0
    output_type: Literal["rgb", "depth", "segmentation", "multi"] = "rgb"


class BuildablesPhysicsManifest(BaseModel):
    schema_version: str = "0.1.0"
    version: int = 1
    updated_at: str | None = None
    project_id: str
    project_name: str
    project_mode: Literal["default_demo", "imported_project"] = "default_demo"
    project_type: Literal["robot_dog", "robot_arm", "wheeled_rover", "gripper", "drone", "mechanism", "imported_cad_assembly", "generic"] = "generic"
    units: Units = Field(default_factory=Units)
    assets: list[Asset] = Field(default_factory=list)
    materials: list[Material] = Field(default_factory=list)
    links: list[Link] = Field(default_factory=list)
    joints: list[Joint] = Field(default_factory=list)
    actuators: list[Actuator] = Field(default_factory=list)
    electronics: list[Electronics] = Field(default_factory=list)
    sensors: list[Sensor] = Field(default_factory=list)
    wires: list[Wire] = Field(default_factory=list)
    collision_primitives: list[CollisionPrimitive] = Field(default_factory=list)
    robot_description: RobotDescription = Field(default_factory=RobotDescription)
    environment: dict = Field(default_factory=dict)
    control: ControlConfig = Field(default_factory=ControlConfig)
    scenarios: list[Scenario] = Field(default_factory=list)
    payloads: list[Payload] = Field(default_factory=list)
    environments: dict = Field(default_factory=dict)
    controls: dict = Field(default_factory=dict)
    tests: list[dict] = Field(default_factory=list)
    render_cameras: list[RenderCamera] = Field(default_factory=list)
    generated_robot_descriptions: dict = Field(default_factory=dict)
    metadata_status: dict = Field(default_factory=dict)
