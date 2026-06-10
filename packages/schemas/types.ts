export type UnitSystem = {
  length: "m";
  mass: "kg";
  time: "s";
  angle: "rad";
};

export type Vec3 = { x: number; y: number; z: number };
export type Transform = { position: Vec3; rotation_rpy: Vec3 };

export type BuildablesAsset = {
  id: string;
  name: string;
  type: "step" | "stl" | "obj" | "glb" | "gltf" | "urdf" | "mjcf" | "texture" | "other";
  file_path: string;
  original_filename: string;
  unit_scale_to_meters: number;
  visual_only: boolean;
  generated: boolean;
  source_asset_id?: string | null;
  notes?: string | null;
};

export type BuildablesMaterial = {
  id: string;
  name: string;
  density_kg_m3: number;
  static_friction: number;
  dynamic_friction: number;
  restitution: number;
  youngs_modulus_pa?: number | null;
  yield_strength_pa?: number | null;
  melting_point_c?: number | null;
  thermal_notes?: string | null;
  simulation_notes: string;
  source_url?: string | null;
  confidence: "placeholder" | "datasheet" | "user_provided";
};

export type BuildablesLink = {
  id: string;
  name: string;
  category: "body" | "leg" | "foot" | "bracket" | "mount" | "electronics_block" | "sensor_mount" | "wire" | "payload" | "other";
  visual_asset_id?: string | null;
  material_id: string;
  mass_kg: number;
  center_of_mass: Vec3;
  inertia_tensor?: number[] | null;
  transform: Transform;
  collision_primitive_ids: string[];
  parent_link_id?: string | null;
  editable: boolean;
  notes?: string | null;
};

export type BuildablesJoint = {
  id: string;
  name: string;
  type: "fixed" | "revolute" | "continuous" | "prismatic" | "ball";
  parent_link_id: string;
  child_link_id: string;
  origin_xyz: Vec3;
  origin_rpy: Vec3;
  axis_xyz: Vec3;
  limit_lower_rad: number;
  limit_upper_rad: number;
  effort_limit_nm: number;
  velocity_limit_rad_s: number;
  damping: number;
  friction: number;
  auto_detected: boolean;
  user_confirmed: boolean;
  notes?: string | null;
};

export type BuildablesActuator = {
  id: string;
  name: string;
  type: "servo" | "dc_motor" | "stepper" | "brushless" | "linear_actuator" | "virtual_motor";
  real_component_profile_id: string;
  joint_id: string;
  control_mode: "position" | "velocity" | "torque";
  max_torque_nm: number;
  max_velocity_rad_s: number;
  rated_voltage_v: number;
  stall_current_a: number;
  mass_kg: number;
  dimensions_m: number[];
  mounting_transform: Transform;
  confidence: "placeholder" | "datasheet" | "manufacturer_page" | "user_provided";
};

export type BuildablesScenario = {
  id: string;
  name: string;
  description: string;
  duration_s: number;
  config: Record<string, unknown>;
};

export type BuildablesElectronics = {
  id: string;
  component_profile_id: string;
  link_id?: string | null;
  transform: Transform;
  editable: boolean;
  notes?: string | null;
};

export type BuildablesSensor = {
  id: string;
  name: string;
  sensor_type: string;
  attach_link_id: string;
  transform: Transform;
  update_rate_hz: number;
  fov_deg?: number | null;
  range_m?: number | null;
  derived: boolean;
};

export type BuildablesWire = {
  id: string;
  name: string;
  from_component_id: string;
  to_component_id: string;
  route_points: Vec3[];
  mass_kg: number;
  min_bend_radius_m: number;
};

export type BuildablesPhysicsManifest = {
  schema_version: "0.1.0";
  version: number;
  updated_at?: string | null;
  project_id: string;
  project_name: string;
  project_mode?: "default_demo" | "imported_project";
  project_type?: "robot_dog" | "robot_arm" | "wheeled_rover" | "gripper" | "drone" | "mechanism" | "imported_cad_assembly" | "generic";
  units: UnitSystem;
  assets: BuildablesAsset[];
  materials: BuildablesMaterial[];
  links: BuildablesLink[];
  joints: BuildablesJoint[];
  actuators: BuildablesActuator[];
  electronics: BuildablesElectronics[];
  sensors: BuildablesSensor[];
  wires: BuildablesWire[];
  collision_primitives: Record<string, unknown>[];
  robot_description: {
    preferred_format: "urdf" | "mjcf";
    urdf_path: string | null;
    mjcf_path: string | null;
    generated_from_manifest: boolean;
  };
  environment: Record<string, unknown>;
  control: Record<string, unknown>;
  scenarios: BuildablesScenario[];
  payloads?: Array<{ id: string; name: string; mass_kg: number; attach_link_id?: string | null; offset?: Transform }>;
  environments?: Record<string, unknown>;
  controls?: Record<string, unknown>;
  tests?: Array<Record<string, unknown>>;
  render_cameras?: Array<{ id: string; name: string; attach_link_id?: string | null; transform?: Transform; fov_deg?: number; output_type?: string }>;
  generated_robot_descriptions?: Record<string, unknown>;
  metadata_status?: Record<string, unknown>;
};
